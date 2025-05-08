cat > install_windows.bat << 'EOF'
@echo off
echo Starting installation for madcrew project...

REM Clone repository if not already done
if not exist "madcrew" (
  git clone https://github.com/archymad/madcrew.git
  cd madcrew
) else (
  echo Repository already exists. Skipping clone.
  cd madcrew
)

REM Create and activate conda environment
call conda create -n mad_crew python=3.10 -y
call conda activate mad_crew

REM Install required packages
pip install crewai langchain anthropic python-dotenv

REM Create project structure if it doesn't exist
if not exist "meta_crew" mkdir meta_crew
if not exist "generated_crews" mkdir generated_crews
if not exist "utils" mkdir utils

REM Display environment information
echo Installation complete! Environment setup:
call conda env list
pip list | findstr "crewai langchain anthropic python-dotenv"

echo You can now start working with the madcrew project.
pause
EOF