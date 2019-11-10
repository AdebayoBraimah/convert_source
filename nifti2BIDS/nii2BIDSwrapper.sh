#!/usr/bin/env bash

# define variables
scriptsDir=$(dirname $(realpath ${0}))

# Echoes status updates to the command line
echo_color(){
  msg='\033[0;'"${@}"'\033[0m'
  # echo -e ${msg} >> ${stdOut} 2>> ${stdErr}
  echo -e ${msg} 
}
echo_red(){
  echo_color '31m'"${@}"
}
echo_green(){
  echo_color '32m'"${@}"
}
echo_blue(){
  echo_color '36m'"${@}"
}

exit_error(){
  echo_red "${@}"
  exit 1
}

# Lists
ids317=/Volumes/ADEBAYO_4/Repo/Scripts/ConvertSource/subLists/scannerNiftis/IRC317/nifti_list_317_IDs.txt
files317=/Volumes/ADEBAYO_4/Repo/Scripts/ConvertSource/subLists/scannerNiftis/IRC317/nifti_list_317.txt
bids317=/Volumes/brac4g/IRC317H/BIDS/RawData

# Create subject Arrays
mapfile -t files < ${files317}
mapfile -t subs < ${ids317}

# nii2BIDS
echo_blue "Processing IRC317"
for ((i = 0; i < ${#subs[@]}; i++)); do
  echo_blue "Processing: sub-${subs[$i]}"
  ${scriptsDir}/nifti2BIDS.sh --data ${files[$i]} --sub ${subs[$i]} --out ${bids317} --ses 1
done

echo_green "Done Processing IRC317!"

unset files 
unset subs 

# Lists
ids287=/Volumes/ADEBAYO_4/Repo/Scripts/ConvertSource/subLists/scannerNiftis/IRC287/nifti_list_287_IDs.txt
files287=/Volumes/ADEBAYO_4/Repo/Scripts/ConvertSource/subLists/scannerNiftis/IRC287/nifti_list_287.txt
bids287=/Volumes/brac4g/IRC287H/BIDS/RawData

# Create subject Arrays
mapfile -t files < ${files287}
mapfile -t subs < ${ids287}

# nii2BIDS
echo_blue "Processing IRC287"
for ((i = 0; i < ${#subs[@]}; i++)); do
  echo_blue "Processing: sub-${subs[$i]}"
  ${scriptsDir}/nifti2BIDS.sh --data ${files[$i]} --sub ${subs[$i]} --out ${bids287} --ses 1
done

echo_green "Done Processing IRC287!"
