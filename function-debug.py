from functions.aws import generate_queue_report

def main():
    try:
        generate_queue_report('old')
    except Exception as e:
        print(f"{e}")

if __name__ == "__main__":
    main()