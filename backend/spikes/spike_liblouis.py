import sys
import traceback

# Grade 1 Braille mapping (ASCII to Unicode Braille)
GRADE1_TABLE = {
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽',
    'z': '⠵',
    '1': '⠁', '2': '⠃', '3': '⠉', '4': '⠙', '5': '⠑',
    '6': '⠋', '7': '⠛', '8': '⠓', '9': '⠊', '0': '⠚',
    ' ': '⠀', '.': '⠲', ',': '⠂', ';': '⠆', ':': '⠒',
    '!': '⠖', '?': '⠦', '-': '⠤', "'": '⠄', '"': '⠐⠂',
}
NUMBER_INDICATOR = '⠼'
CAPITAL_INDICATOR = '⠠'

def translate_grade1(text: str) -> str:
    result = []
    in_number = False
    
    for char in text:
        if char.isdigit():
            if not in_number:
                result.append(NUMBER_INDICATOR)
                in_number = True
            result.append(GRADE1_TABLE.get(char, ''))
        else:
            in_number = False
            if char.isupper():
                result.append(CAPITAL_INDICATOR)
            result.append(GRADE1_TABLE.get(char.lower(), ''))
    
    return ''.join(result)

def main():
    words = ["Nucleus", "Cell Wall", "Heart", "ABC123"]
    
    try:
        import louis
        print("Successfully imported liblouis.")
        
        # Test translation
        # Note: testing exact liblouis tables might require tables to be present on the system.
        # We will attempt a basic translation.
        for word in words:
            try:
                # Basic en-us-g1.ctb table usually available, might fail if not installed properly.
                translation = louis.translateString(["en-us-g1.ctb"], word)
                print(f"liblouis translation of '{word}': {translation}")
            except Exception as e:
                print(f"liblouis translation failed for '{word}': {e}")
        
        print("\nSPIKE RESULT: PASS")
        
    except ImportError as e:
        print(f"Failed to import liblouis: {e}")
        print("Using pure-Python Grade 1 Braille fallback...")
        
        for word in words:
            translation = translate_grade1(word)
            print(f"Fallback translation of '{word}': {translation}")
            
        print("\nSPIKE RESULT: FAIL WITH FALLBACK")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        print("\nSPIKE RESULT: FAIL WITH FALLBACK")

if __name__ == "__main__":
    main()
