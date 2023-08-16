import os
import sys


from tokenize import tokenize, NAME, OP

def get_args_in_src(test_file):
    args = {'exit_on_fail': True}
    with open(test_file,"rb") as f:
        try:
            tokens = list(tokenize(f.readline))
            for n in range(0, len(tokens)):
                token = tokens[n]
                if token[0] == NAME and token[1] == "args" and n < (len(tokens)-2):
                    op_token = tokens[n+1]
                    arg_token = tokens[n+2]
                    if op_token[0] == OP and op_token[1] == "[" \
                      and arg_token[0] == NAME:
                        args[arg_token[1]] = True
        except Exception as e:
            raise Exception('Failed to parse file "%s":\n\t%s' % (os.path.basename(test_file), str(e)))
    return args


def get_test_doc(test_file):
    with open(test_file,"r") as f:
        lines = f.readlines()
        header_comment_open = False
        doc_lines = []
        for line in lines:
            if line.startswith('"""') or line.startswith("'''"):
                line = line.replace("'''","")
                line = line.replace('"""','')
                if not header_comment_open:
                    header_comment_open = True
                else:
                    break
            if header_comment_open and (len(doc_lines) or len(line) > 1):
                doc_lines += [line]
        return "".join(doc_lines)
