# ============================================
# Photo Tool - Windows Firewall Setup
# ============================================
# Run as Administrator!
# Right-click → "Run with PowerShell"
# ============================================

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "📺 Photo Tool - Smart TV Firewall Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "How to run as Administrator:" -ForegroundColor Yellow
    Write-Host "1. Right-click on this script" -ForegroundColor Yellow
    Write-Host "2. Select 'Run with PowerShell' or 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Running as Administrator" -ForegroundColor Green
Write-Host ""

# Step 1: Check if rule already exists
Write-Host "Step 1: Checking existing firewall rules..." -ForegroundColor Yellow

$existingRule = Get-NetFirewallRule -DisplayName "Photo Tool Web GUI" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "⚠️  Firewall rule already exists!" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Do you want to recreate it? (y/n)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Removing old rule..." -ForegroundColor Yellow
        Remove-NetFirewallRule -DisplayName "Photo Tool Web GUI"
        Write-Host "✓ Old rule removed" -ForegroundColor Green
    } else {
        Write-Host "Keeping existing rule" -ForegroundColor Yellow
        $existingRule | Format-List DisplayName, Enabled, Direction, Action, Protocol, LocalPort
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 0
    }
}

# Step 2: Create firewall rule
Write-Host ""
Write-Host "Step 2: Creating firewall rule for port 8000..." -ForegroundColor Yellow

try {
    netsh advfirewall firewall add rule name="Photo Tool Web GUI" dir=in action=allow protocol=TCP localport=8000 | Out-Null
    Write-Host "✓ Firewall rule created successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create firewall rule: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 3: Verify rule
Write-Host ""
Write-Host "Step 3: Verifying firewall rule..." -ForegroundColor Yellow

$newRule = Get-NetFirewallRule -DisplayName "Photo Tool Web GUI" -ErrorAction SilentlyContinue

if ($newRule) {
    Write-Host "✓ Firewall rule is active!" -ForegroundColor Green
    Write-Host ""
    $newRule | Format-List DisplayName, Enabled, Direction, Action, Protocol, LocalPort
} else {
    Write-Host "❌ Firewall rule not found after creation!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 4: Get local IP address
Write-Host ""
Write-Host "Step 4: Getting your PC's IP address..." -ForegroundColor Yellow

$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like '*Wi-Fi*' -or $_.InterfaceAlias -like '*Ethernet*' -or $_.InterfaceAlias -like '*WLAN*'} | Select-Object -First 1).IPAddress

if ($localIP) {
    Write-Host "✓ Local IP Address: $localIP" -ForegroundColor Green
} else {
    Write-Host "⚠️  Could not determine local IP address automatically" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run this command to find your IP:" -ForegroundColor Yellow
    Write-Host "ipconfig | findstr IPv4" -ForegroundColor Cyan
    $localIP = "192.168.x.xxx"
}

# Step 5: Test if port is available
Write-Host ""
Write-Host "Step 5: Checking if port 8000 is available..." -ForegroundColor Yellow

$portInUse = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host "✓ Server is already running on port 8000" -ForegroundColor Green
} else {
    Write-Host "⚠️  Server is not running yet (this is OK)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Start the server:" -ForegroundColor White
Write-Host "   cd C:\_Git\Python-tools" -ForegroundColor Cyan
Write-Host "   python gui_poc/server.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. On your Smart TV:" -ForegroundColor White
Write-Host "   Open Browser and navigate to:" -ForegroundColor White
Write-Host "   http://$localIP:8000" -ForegroundColor Green
Write-Host ""
Write-Host "3. Test on PC first:" -ForegroundColor White
Write-Host "   http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
