#!/bin/bash

# $1 - input dir
# $2 - output dir
# $3 - models dir (/media/data)
# $4 - parser dir ($HOME)


INDIR=$1
OUTDIR=$2

MODELS=$3
DIR=$4
SOURCE=$4/source
SYSTEM=$4/system
TEMP=$SYSTEM/temp
MEM=14000
SUCCESS=$SYSTEM/successful.txt

for f in $(cat $INDIR/metadata.json | tr -d '[]\n ' | sed 's/},{/\n/g' | tr -d '{}'); do 
    LCODE=$(echo $f | tr ',' '\n' | grep '"lcode"' | cut -d ':' -f 2 | tr -d '"')
    TCODE=$(echo $f | tr ',' '\n' | grep '"tcode"' | cut -d ':' -f 2 | tr -d '"')
    if [ $TCODE == '0' ]; then
        LNGCODE=$LCODE
    else
        LNGCODE=$LCODE'-'$TCODE
    fi
    LNG=$(cat $MODELS/lng_codes.txt | egrep "^"$LNGCODE":" | cut -d ':' -f 2)
    if [ $LNG=='' ]; then
        LNGCODE=$LCODE
        LNG=$(cat $MODELS/lng_codes.txt | egrep "^"$LNGCODE":" | cut -d ':' -f 2)
    fi

    SRES=$(cat $SUCCESS | grep "^$LNGCODE$" | wc -l);
    if [ $SRES -gt 0 ]; then
        continue;
    fi
    
    INPUT=$(echo $f | tr ',' '\n' | grep 'psegmorfile' | cut -d ':' -f 2 | tr -d '"')
    OUTPUT=$(echo $f | tr ',' '\n' | grep 'outfile' | cut -d ':' -f 2 | tr -d '"')
    
    echo 'Language: '$LCODE'-'$TCODE
    echo 'Model: '$LNG

    if [ -f $MODELS/$LNG/run_surprise.sh ]; then
        echo 'start surprise language script'
        timeout 30m $MODELS/$LNG/run_surprise.sh $INDIR/$INPUT $OUTDIR/$OUTPUT
        echo 'Surprise language script done'
    else
        PARSES=""
        WEIGHTS=""
    
        # UDPipe
        if [ -f $MODELS/$LNG/udpipe/model.* ]; then
            MODEL=$MODELS/$LNG/udpipe/model.*
            echo 'Start udpipe'
            timeout 30m cat $INDIR/$INPUT | cut -f1-2 | sed 's/$/\t_\t_\t_\t_\t_\t_\t_\t_/g' | sed 's/^\t.*//' | sed 's/\(#[^\t]*\)\t[^$]*$/\1/' | $SOURCE/udpipe/src/udpipe --tag --parse $MODEL  > $TEMP/$OUTPUT.udpipe
            echo 'UDPipe done'
            if [ -f $TEMP/$OUTPUT.udpipe ]; then
                PARSES=$TEMP/$OUTPUT.udpipe" "
                if [ -f $SYSTEM/models/$LNG/udpipe/weight ]; then
                    WEIGHTS=$(cat $SYSTEM/models/$LNG/udpipe/weight)" "
                else
                    WEIGHTS="1 "
                fi
            fi
        fi
        
        # MarMoT
        if [ -f $MODELS/$LNG/marmot/model.marmot ]; then
            MODEL=$MODELS/$LNG/marmot/model.marmot
            echo 'Start MarMoT'
            timeout 30m $SYSTEM/scripts/marmot-tag.sh $MODEL $INDIR/$INPUT $TEMP/$OUTPUT.marmot
            echo 'MarMoT done'
            BISTINPUT=$TEMP/$OUTPUT.marmot
        fi
        if [ ! -f $TEMP/$OUTPUT.marmot ]; then
            BISTINPUT=$TEMP/$OUTPUT.udpipe
        fi
        
        # BIST (graph-based)
        if [ -f $MODELS/$LNG/bist_graph/neuralfirstorder.* ]; then
            MODEL=$MODELS/$LNG/bist_graph/neuralfirstorder.*
            PICKLE=$MODELS/$LNG/bist_graph/*.pickle
            echo 'Start BIST (graph-based)'
            timeout 30m python $SOURCE/bist-parser/bmstparser/src/parser.py --predict --outdir $TEMP --test $BISTINPUT --model $MODEL --params $PICKLE --dynet-mem $MEM
            echo 'BIST (graph-based) done'
            if [ -f $TEMP/test_pred.conll ]; then
                mv $TEMP/test_pred.conll $TEMP/$OUTPUT.graph 
            else
                mv $TEMP/test_pred.conllu $TEMP/$OUTPUT.graph 
            fi
            
            if [ -f $TEMP/$OUTPUT.graph ]; then
                PARSES=$PARSES" "$TEMP/$OUTPUT.graph" "
                if [ -f $SYSTEM/models/$LNG/bist_graph/weight ]; then
                    WEIGHTS=$WEIGHTS$(cat $SYSTEM/models/$LNG/bist_graph/weight)" "
                else
                    WEIGHTS=$WEIGHTS"1 "
                fi
            fi
        fi
        
        # BIST (transition-based)        
        if [ -f $MODELS/$LNG/bist_transition/barchybrid.* ]; then
            MODEL=$MODELS/$LNG/bist_transition/barchybrid.*
            PICKLE=$MODELS/$LNG/bist_transition/*.pickle
            echo 'Start BIST (transition-based)'
            if [ -f $MODELS/$LNG/embedding/*.vec ]; then
                EMBEDDINGS=$MODELS/$LNG/embedding/*.vec
                timeout 30m python $SOURCE/bist-parser/barchybrid/src/parser.py --predict --outdir $TEMP --test $BISTINPUT --model $MODEL --params $PICKLE --dynet-mem $MEM --extrn $EMBEDDINGS
            else
                timeout 30m python $SOURCE/bist-parser/barchybrid/src/parser.py --predict --outdir $TEMP --test $BISTINPUT --model $MODEL --params $PICKLE --dynet-mem $MEM
            fi
            echo 'BIST (transition-based) done'
            if [ -f $TEMP/test_pred.conll ]; then
                mv $TEMP/test_pred.conll $TEMP/$OUTPUT.transition 
            else
                mv $TEMP/test_pred.conllu $TEMP/$OUTPUT.transition 
            fi
            
            if [ -f $TEMP/$OUTPUT.transition ]; then
                PARSES=$PARSES" "$TEMP/$OUTPUT.transition" "
                if [ -f $SYSTEM/models/$LNG/bist_transition/weight ]; then
                    WEIGHTS=$WEIGHTS$(cat $SYSTEM/models/$LNG/bist_transition/weight)" "
                else
                    WEIGHTS=$WEIGHTS"1 "
                fi        
            fi
        fi
        
        # Voting
        echo 'Start voting'
        timeout 30m python3 $SYSTEM/scripts/vnew_voting.py -p $PARSES -w $WEIGHTS -o $TEMP/$OUTPUT.voting
        echo 'Voting done'
        
        if [ -f $TEMP/$OUTPUT.voting ]; then
            # Remove multiple roots
            echo 'Remove multiple roots'
            timeout 30m python $SYSTEM/scripts/remove_two_roots.py -o $TEMP/$OUTPUT.voting
            echo 'Multiple roots removed'
        else
            if [ -f $TEMP/$OUTPUT.udpipe ]; then
                echo 'Remove multiple roots'
                timeout 30m python $SYSTEM/scripts/remove_two_roots.py -o $TEMP/$OUTPUT.udpipe
                echo 'Multiple roots removed'
            else
                if [ -f $TEMP/$OUTPUT.graph ]; then
                    echo 'Remove multiple roots'
                    timeout 30m python $SYSTEM/scripts/remove_two_roots.py -o $TEMP/$OUTPUT.graph
                    echo 'Multiple roots removed'
                else
                    echo 'Remove multiple roots'
                    timeout 30m python $SYSTEM/scripts/remove_two_roots.py -o $TEMP/$OUTPUT.transition
                    echo 'Multiple roots removed'
                fi
            fi
        fi
        cat $TEMP/$OUTPUT.voting_no2root | cut -f 1-10 > $OUTDIR/$OUTPUT
            
    fi
    #rm $TEMP/*
done

