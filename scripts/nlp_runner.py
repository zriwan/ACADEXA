# test_nlp_runner.py
from nlp.nlp_processor import parse_command

while True:
    try:
        cmd = input("\nType a command (or 'q' to quit): ")
        if cmd.lower().strip() == "q":
            break
        result = parse_command(cmd)
        print("Parsed:", result.model_dump())
    except KeyboardInterrupt:
        break
