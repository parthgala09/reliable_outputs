from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

from messy_inputs import MESSY_INPUTS
from repair_loop import repair_loop


def main() -> None:
    for i, sample in enumerate(MESSY_INPUTS, start=1):
        print(f"--- Sample {i} ---")
        print(sample)
        try:
            card = repair_loop(sample)
            print("Parsed ContactCard:")
            pprint(card.model_dump())
        except Exception as exc:
            print("Failed to parse contact card:", exc)
        print()


if __name__ == "__main__":
    main()
