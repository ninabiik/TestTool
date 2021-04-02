import argparse

class CommandLineInterface:

    def __init__(self):
        pass

    def get_arguments(self):

        args_parser = argparse.ArgumentParser()

        required_file_args = args_parser.add_argument_group('required arguments')
        required_file_args.add_argument('--firstenv', default="dev", help="Environment: [dev, qa, uat, prod]", required=True)
        required_file_args.add_argument('--secondenv', default="uat", help="Environment: [dev, qa, uat, prod]", required=True)
        required_file_args.add_argument('--inputfile', default="InputFile.xlsx", help="Input filex in excel format, sheet name must be 'Mapping'", required=False)

        args = args_parser.parse_args()

        self.firstenv = args.firstenv.lower()
        self.secondenv = args.secondenv.lower()
        self.inputfile = args.inputfile

        return_args_dict = {
            "firstenv": self.firstenv,
            "secondenv": self.secondenv,
            'inputfile': self.inputfile
        }

        return return_args_dict
