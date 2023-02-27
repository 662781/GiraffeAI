# Set the Python version and path
$pythonVersion = "310"
$pythonPath = "C:\Python$pythonVersion\python.exe"

if (Test-Path $pythonPath) {
    Write-Host "Path exists."
} else {
    Write-Host "Path does not exist."
    $pythonPath = "py"
}

# Create the virtual environment
& Set-Location .\src
& $pythonPath -m venv venv

# Activate the virtual environment
& "venv\Scripts\Activate.ps1"

# Install dependencies from requirements.txt & update pip
& pip install -r requirements.txt
& py -m pip install --upgrade pip