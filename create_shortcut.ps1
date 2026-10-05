$targetExe = "C:\Users\sinan.nergiz\.gemini\antigravity-ide\scratch\essek\dist\TJK_RACING_AI_PRO_v2.exe"
$workingDir = "C:\Users\sinan.nergiz\.gemini\antigravity-ide\scratch\essek\dist"

$desktop1 = [System.Environment]::GetFolderPath('Desktop')
$desktop2 = "$env:USERPROFILE\Desktop"
$desktop3 = "$env:USERPROFILE\OneDrive - Stftex\Masaüstü"

$paths = @($desktop1, $desktop2, $desktop3) | Select-Object -Unique

$wshShell = New-Object -ComObject WScript.Shell

foreach ($d in $paths) {
    if (Test-Path $d) {
        $shortcutPath = Join-Path $d "essek.lnk"
        $shortcut = $wshShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $targetExe
        $shortcut.WorkingDirectory = $workingDir
        $shortcut.Description = "essek - TJK At Yarışı Yapay Zeka Tahmin Platformu"
        $shortcut.Save()
        Write-Host "Kısayol oluşturuldu: $shortcutPath"
    }
}
