"""
Barcha UTF-16 fayllarni UTF-8 ga o'tkazadi.
Windows'da ishga tushiring: python fix_encoding.py
"""
import os
import sys

def fix_file(path):
    try:
        with open(path, 'rb') as f:
            raw = f.read()
        
        # Null bytes bor => UTF-16 LE (BOM siz)
        if b'\x00' in raw:
            # Try UTF-16 with BOM first, then LE
            try:
                text = raw.decode('utf-16')
            except UnicodeDecodeError:
                text = raw.decode('utf-16-le')
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"  [OK] {path}")
            return True
        return False
    except Exception as e:
        print(f"  [XATO] {path}: {e}")
        return False

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    print(f"Papka: {base}\n")
    
    fixed = 0
    for root, dirs, files in os.walk(base):
        # Skip .git
        dirs[:] = [d for d in dirs if d != '.git']
        for fname in files:
            if fname.endswith(('.py', '.txt', '.md', '.env', '.example', '.gitignore')):
                path = os.path.join(root, fname)
                if fix_file(path):
                    fixed += 1
    
    print(f"\nJami {fixed} ta fayl tuzatildi.")
    if fixed == 0:
        print("Hamma fayl allaqachon to'g'ri formatda.")

if __name__ == '__main__':
    main()
