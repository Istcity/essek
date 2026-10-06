import os
import sys
import subprocess

def create_shortcut(target_exe=None):
    try:
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_dir):
            desktop_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
            
        if not target_exe or not os.path.exists(target_exe):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_exe = os.path.join(base_dir, "dist", "TJK_RACING_AI_PRO_v2.exe")
            
        shortcut_path = os.path.join(desktop_dir, "TJK AI At Yarışı Tahmin Platformu.lnk")
        work_dir = os.path.dirname(target_exe)
        
        ps_commands = [
            '$WshShell = New-Object -ComObject WScript.Shell',
            f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')",
            f"$Shortcut.TargetPath = '{target_exe}'",
            f"$Shortcut.WorkingDirectory = '{work_dir}'",
            "$Shortcut.Description = 'TJK AI At Yarışı Tahmin ve Analiz Platformu PRO v2.0'",
            f"$Shortcut.IconLocation = '{target_exe},0'",
            '$Shortcut.Save()'
        ]
        
        full_ps = "; ".join(ps_commands)
        res = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", full_ps], capture_output=True, text=True)
        
        if os.path.exists(shortcut_path):
            print(f"[OK] Masaüstü Kısayolu Başarıyla Oluşturuldu: {shortcut_path}")
            return True, shortcut_path
        else:
            print(f"[FAIL] Kısayol oluşturulamadı: {res.stderr}")
            return False, res.stderr
    except Exception as e:
        print(f"[ERROR] Hata: {e}")
        return False, str(e)

if __name__ == '__main__':
    create_shortcut()
