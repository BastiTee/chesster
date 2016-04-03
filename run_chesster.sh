#!/bin/bash

show_help () {
	echo -e "\nUsage: `basename $0` [-s <SCRIPT>] \n"
	echo -e "\t-s <SCRIPT>\t\tChesster script to run\n"
	echo -e "Supported scripts:\n"
	for script in $( python -m chesster ); do
		echo $script 
	done | sed -r -e "s/^[^_]+_/\t/g"
	echo
	exit 1
}


RUNSCRIPT=$1

[ -v $( command -v python ) ] && { echo "No python installed."; show_help; }
[ -v $RUNSCRIPT ] && { echo "No script selected."; show_help; }

# EXTEND PYTHONOPATH
for ext_proj in $( find ../ -iname "requirements.txt" | grep -v "chesster-github" | sed -e "s/\/requirements.txt//g" )
do 
	# echo "Adding project '$ext_proj' to PYTHONPATH"
	ext_proj=$( readlink -f $ext_proj )
	if [ -v $PYTHONPATH ]
	then
		export PYTHONPATH="$ext_proj" 
	else
		export PYTHONPATH="${PYTHONPATH}:$ext_proj"
	fi
done
# echo "PYTHONPATH=${PYTHONPATH}"

shift
python chesster/chesster_${RUNSCRIPT}.py $@
[ $? == 2 ] && { echo "Script '$RUNSCRIPT' does not exist."; show_help; }


