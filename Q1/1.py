def encrypt_char(c, shift1, shift2):
    if c.islower():
        if 'a' <= c <= 'm':
            return chr((ord(c) - ord('a') + shift1 * shift2) % 26 + ord('a'))
        elif 'n' <= c <= 'z':
            return chr((ord(c) - ord('a') - (shift1 + shift2)) % 26 + ord('a'))
    elif c.isupper():
        if 'A' <= c <= 'M':
            return chr((ord(c) - ord('A') - shift1) % 26 + ord('A'))
        elif 'N' <= c <= 'Z':            
            return chr((ord(c) - ord('A') + shift2**2) % 26 + ord('A'))
    return c

def decrypt_char(c_enc, shift1, shift2):
    if c_enc.islower():
        c_val = ord(c_enc) - ord('a')
        orig1 = (c_val - shift1 * shift2) % 26
        orig2 = (c_val + shift1 + shift2) % 26
    
        if 0 <= orig1 <= 12:
            return chr(orig1 + ord('a'))
        else:
            return chr(orig2 + ord('a'))
    elif c_enc.isupper():
        c_val = ord(c_enc) - ord('A')
        orig1 = (c_val + shift1) % 26
        orig2 = (c_val - shift2**2) % 26
        if 0 <= orig1 <= 12:
            return chr(orig1 + ord('A'))
        else:
            return chr(orig2 + ord('A'))
    return c_enc

def encrypt_file(shift1, shift2):
    try:
        with open("raw_text.txt", "r") as f:
            content = f.read()
        encrypted = "".join(encrypt_char(c, shift1, shift2) for c in content)
        with open("encrypted_text.txt", "w") as f:
            f.write(encrypted)
        print("Encryption complete. Saved to 'encrypted_text.txt'.")
    except FileNotFoundError:
        print("Error: 'raw_text.txt' not found.")

def decrypt_file(shift1, shift2):
    try:
        with open("encrypted_text.txt", "r") as f:
            content = f.read()
        decrypted = "".join(decrypt_char(c, shift1, shift2) for c in content)
        with open("decrypted_text.txt", "w") as f:
            f.write(decrypted)
        print("Decryption complete. Saved to 'decrypted_text.txt'.")
    except FileNotFoundError:
        print("Error: 'encrypted_text.txt' not found.")

def verify_decryption():
    try:
        with open("raw_text.txt", "r") as f1, open("decrypted_text.txt", "r") as f2:
            raw = f1.read()
            decrypted = f2.read()
        if raw == decrypted:
            print("Verification successful: Decrypted text matches original raw text.")
        else:
            print("Verification failed: Decrypted text does not match original raw text.")
    except FileNotFoundError:
        print("Error: Required files for verification not found.")

if __name__ == "__main__":
    print("--- Text Encryptor/Decryptor ---")
    try:
        s1 = int(input("Enter shift1 value: "))
        s2 = int(input("Enter shift2 value: "))
        encrypt_file(s1, s2)
        decrypt_file(s1, s2)
        verify_decryption()
    except ValueError:
        print("Invalid input. Please enter integers for shift values.")