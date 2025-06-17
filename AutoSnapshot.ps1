param (
    [string]$vmxPath = "C:\Path\To\VMX\File.vmx",
    [int]$maxSnapshots = 5
)

function Take-Snapshot {
    param([string]$vmxPath)

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $snapshotName = "AutoSnapshot_$timestamp"
    Write-Host "Creating snapshot: $snapshotName"
    & "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"  -T ws snapshot "$vmxPath" "$snapshotName"
}

function Get-AutoSnapshots {
    param([string]$vmxPath)

    $snapshotList = & "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"  -T ws listSnapshots "$vmxPath" 2>$null
    $snapshots = @()

    foreach ($line in $snapshotList) {
        if ($line -match "^AutoSnapshot_") {
            $snapshots += $line.Trim()
        }
    }

    return $snapshots | Sort-Object -Descending
}

function Prune-OldSnapshots {
    param(
        [string]$vmxPath,
        [int]$keepCount
    )

    $autoSnapshots = Get-AutoSnapshots -vmxPath $vmxPath
    if ($autoSnapshots.Count -gt $keepCount) {
        $toRemove = $autoSnapshots[$keepCount..($autoSnapshots.Count - 1)]
        foreach ($snap in $toRemove) {
            Write-Host "Deleting old snapshot: $snap"
            & "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"  -T ws deleteSnapshot "$vmxPath" "$snap"
        }
    }
}

# Check if VM is running
$runningVMs = & "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"  -T ws list | Select-String -SimpleMatch "$vmxPath"
$isRunning = $runningVMs -ne $null

if ($isRunning) {
    Write-Host "VM is running. Suspending..."
    
    # Suspend in separate process to avoid freeze
    Start-Process -FilePath "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"  -ArgumentList @('-T', 'ws', 'suspend', "`"$vmxPath`"", 'soft') -Wait

    # Wait until VM is fully suspended
    do {
        Start-Sleep -Seconds 2
        $vmList = & "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"  -T ws list
        $isStillRunning = $vmList -like "*$vmxPath*"
        Write-Host "Waiting for VM to suspend..."
    } while ($isStillRunning)

    # Check if VMware Workstation GUI is frozen
    $vmwareProc = Get-Process -Name "vmware" -ErrorAction SilentlyContinue
    if ($vmwareProc -and $vmwareProc.Responding -eq $false) {
        Write-Host "VMware Workstation is not responding. Terminating..."
        Stop-Process -Id $vmwareProc.Id -Force
        Start-Sleep -Seconds 3
    }

    # Take snapshot
    Take-Snapshot -vmxPath $vmxPath

    # Try to start the VM again
    try {
        Write-Host "Starting VM..."
        & "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"  -T ws start "$vmxPath"
    } catch {
        Write-Warning "Failed to start VM. Please check VMware Workstation manually."
    }

} else {
    Write-Host "VM is not running. Taking snapshot..."
    Take-Snapshot -vmxPath $vmxPath
}

# Cleanup old auto-snapshots
Prune-OldSnapshots -vmxPath $vmxPath -keepCount $maxSnapshots
