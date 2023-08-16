import os
import sys


from tokenize import tokenize, NAME, OP, STRING

def get_args_in_src(test_file):
    args = {'exit_on_fail': True}
    with open(test_file,"rb") as f:
        try:
            tokens = list(tokenize(f.readline))
            for n in range(0, len(tokens)):
                token = tokens[n]
                if token.type == NAME and token.string == "args":
                    op_token = tokens[n+1]
                    arg_token = tokens[n+2]
                    if op_token.type == OP and op_token.string == "[" \
                       and arg_token.type == STRING:
                        name = arg_token.string
                        name = "".join([c if c not in "\"'" else '' \
                                       for c in name])
                        args[name] = True
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
