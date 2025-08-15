<#
Equity Index Management Rebalance
Script for executing Python based selections

Central location https://gitlab.ad.solactive.com/epd-ops-transition/templates/infrastructure_eqrebal

See https://solactive.atlassian.net/wiki/spaces/EQOP/pages/41502174/Selection+Process+using+python for more information

Code below in index agnostic and relies on a standard folder structure

Folder structure
  selection from gitbalb 
      <common home>\<selection name>\gitlab
        E.g. T:\EquityOps\REBALANCE\ANPASSUNGEN\A_TEST_INDEX_EQREBTEST1\gitlab
  python viurtual environemtn
      %USERPROFILE%\code\all-my-venvs\_venv<pyver>-<selection folder name> 
#>

$user = (Get-ChildItem Env:\USERNAME).Value
$computername = (Get-ChildItem Env:\COMPUTERNAME).Value
new-Item -type Directory -Path logging -ErrorAction SilentlyContinue
$stamp = (Get-Date).ToString("yyyy-MM-dd--HH-mm-ss")
Start-Transcript -Path "logging\logging-${stamp}-${user}-powershell.log" 

$pysysver=python -c "import sys;print(''.join(sys.version.split('.')[0:2]))"
$current_folder = $PSScriptRoot

write-output "Default configuration"
write-output "computername: $computername"
write-output "user: $user"
write-output "pysysver: $pysysver ( this is python version used by default )"
write-output "current_folder: $current_folder"

function Run-Selection {
    [CmdletBinding()]
    param (
        [string]$ParamPythonHome
    )
    
    write-output "PythonHome : $ParamPythonHome ( this path will be placed at the top of PATH"
    $Env:PATH = "$ParamPythonHome\Scripts" + ";" + "$ParamPythonHome" + ";" + $Env:PATH
    $pysysver=python -c "import sys;print(''.join(sys.version.split('.')[0:2]))"
    write-output "updated pysysver: $pysysver ( this python version will be used through the script below)"

    #program path

    $selection_folder = $current_folder
    # $selection_folder = split-path  $current_folde
    $selection_name = split-path -leaf $selection_folder
    $host.ui.RawUI.WindowTitle = $selection_name

    $selection_code= $current_folder + '\'  + "gitlab"

    # $pysysver

    $venv_name = "_venv" + $pysysver + "-" + $selection_name
    $userprofile = (Get-ChildItem Env:\USERPROFILE).Value

    #path of venv
    $venv_path = $userprofile+"\code\all-my-venvs"
    $venv_folder_path = $venv_path+'\'+$venv_name



    $requirements = $selection_code+"\requirements.txt"

    #checking if venv exists and making one if not
    if  (!(Test-Path -Path $venv_folder_path))
    {   
        #creating venv
        write-output "Virtual environement for selection $selection_name doesn't exists and will be created. "
        &python -m venv $venv_folder_path   

    }

    if  (!(Test-Path -Path "$venv_folder_path\Scripts\activate.ps1"))
    {   
        Write-Error "Virtual environement for selection $selection_name doesn't exist. See error messages above.`nPlease press any key to exit..."
        pause
        exit 1
    }

    write-output "==============================================="

    # activate virtual environment
    &$venv_folder_path\Scripts\activate.ps1
    write-output "==============================================="

    $pyvenvver=python -c "import sys;print(''.join(sys.version.split('.')[0:2]))"
    write-output "pyvenvver: $pyvenvver"

    &python -m pip install --upgrade pip

    #adding requirements
    $sw = [Diagnostics.Stopwatch]::StartNew()
    &python.exe -m pip install -r $requirements
    $sw.Stop()
    $venv_setup_runtime = $sw.Elapsed
    write-output "`n`n" "Requirements installed/updated in virtual environement "  $venv_setup_runtime "`n`n"

    $selection_script_name = "run.py"
    $currentscript= $selection_code + '\' + $selection_script_name

    if (Test-Path -Path $currentscript -PathType Leaf) {
      write-output "$currentscript exists"
     }
     else {
        $selection_script_name = "selection.py"
     }
    $currentscript= $selection_code + '\' + $selection_script_name
    write-output "selection_script_name = $selection_script_name"
    write-output "selection_code = $selection_code"
         

    $config_rebal_path = $selection_code+"\config\template\config_eqrebal.ini"
    $logging_rebal_path = $selection_code+"\config\template\logging_eqrebal.ini"

    if (Test-Path -Path $config_rebal_path -PathType Leaf) {
      Copy-Item "$config_rebal_path" -Destination "$selection_code\config\config.ini"
      write-output "$config_rebal_path copied to $selection_code\config\config.ini"
     }
    # If the file already exists, show the message and do nothing.
     else {
         write-output $config_rebal_path " does not exist"
     }

    if (Test-Path -Path $logging_rebal_path -PathType Leaf) {
      Copy-Item "$logging_rebal_path" -Destination "$selection_code\config\logging.ini"
      write-output "$logging_rebal_path copied to $selection_code\config\logging.ini"
     }
    # If the file already exists, show the message and do nothing.
     else {
         write-output $logging_rebal_path " does not exist"
     }
     


    $sw = [Diagnostics.Stopwatch]::StartNew()
    write-output "`n" "Executing selection..." "`n"
    python.exe $currentscript --repo_name $selection_name
    write-output "`n" "Selection done" "`n"
    $sw.Stop()
    $selection_runtime = $sw.Elapsed
    write-output "`n`n" "Selection runtime "  $selection_runtime "`n`n"
    #pause for the finish (if error accurs)

}

$index_python38 = "c:\python38"

if (Test-Path -Path "$index_python38") {
    write-output "Using $index_python38 to run selection code"
    Run-Selection "$index_python38"


 }
# If the file already exists, show the message and do nothing.
 else {
  write-output "ERROR: $index_python38 does not exist. Raise a ticket with IT to install"
 }

Stop-Transcript 
pause
