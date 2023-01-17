
#!/usr/bin/python3

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import subprocess
import shlex
import re
from typing import List 

app = Flask(__name__)

host ="https://cpp2latex.pythonanywhere.com/"
app.config["UPLOAD_FOLDER"] = "/home/instructions/dic/static/dic_temp_files/"

@app.route('/')
def upload_file():
    return render_template('index.html')



@app.route('/display', methods = ['GET', 'POST'])
def save_file():
    if request.method == 'POST':
        input_func=request.form['code']

        input_func=input_func.replace("_", "")
        input_func=input_func.replace("\t", " ")

        latex_code = """
        \\documentclass[12pt,a4paper]{article}
        \\usepackage{algorithm}
        \\usepackage{algpseudocode}
        \\begin{document}
        \\begin{algorithm}
        """


        def extract_func_info(input_func):
            func_name = re.search("(\w+)\s*\(", input_func).group(1)
            parameters = re.search("\((.*)\)", input_func).group(1)
            # parameter_list = parameters.split(",")
            # parameter_list = [x.strip() for x in parameter_list]
            return func_name, parameters

        func_name, parameter_list = extract_func_info(input_func)
        # print(func_name)  # Output: "add"
        # print(parameter_list)  # Output: ["int a", "int b"]

        def camel_to_sentence(camel_case_word):
            camel_case_word=camel_case_word[0].upper()+camel_case_word[1:]
            parts = re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', camel_case_word)
            parts = [part.capitalize() for part in parts]
            return ' '.join(parts)

        latex_caption = camel_to_sentence(func_name)

        latex_code += f"\\caption{{{latex_caption}}}\n"

        latex_code += "\\begin{algorithmic}[1]\n"
        latex_code += f"\\Procedure{{{func_name}}}{{{parameter_list}}}\n"

        def add_space(input_func):
            return re.sub(r"([^\w\s=_&|/])(\w|\b)", r"\1 \2", re.sub(r"(\w|\b)([^\w\s=_&|/])", r"\1 \2", input_func))

        input_func = add_space(input_func)
        # print(input_func)

        def replace_comments(input_func):
            return re.sub(r"//", "// ", input_func)

        input_func = replace_comments(input_func)

        def extract_function_body(input_func):
            start = input_func.index("{") + 1
            end = input_func.rindex("}")
            return input_func[start:end]

        function_body = extract_function_body(input_func)

        def add_space(input_func):
            return re.sub(r"(\w)([^\w\s])", r"\1 \2", input_func)

        function_body=add_space(function_body)

        def tokenize(input_func):
            tokens = []
            input_func = re.sub("\n", " \n \\\State ", input_func)
            current_token = ""
            paranthesis_count = 0
            for char in input_func:
                if char == "(":
                    paranthesis_count += 1
                    current_token += char
                elif char == ")":
                    paranthesis_count -= 1
                    current_token += char
                    if paranthesis_count == 0:
                        tokens.append(current_token)
                        current_token = ""
                elif char == " " and paranthesis_count == 0:
                    if current_token:
                        tokens.append(current_token)
                        current_token = ""
                else:
                    current_token += char
            if current_token:
                tokens.append(current_token)
            return tokens


        def remove_semi(tokens):
            return [token for token in tokens if token != ';']

        def remove_open(tokens):
            return [token for token in tokens if token != '{']

        tokens = tokenize(function_body)
        tokens=remove_semi(tokens)
        tokens=remove_open(tokens)
        # print(tokens)

        def replace_comments(tokens):
            for i in range(len(tokens)):
                if tokens[i] == "//":
                    tokens[i] = "\\Comment{"
                    for j in range(i+1, len(tokens)):
                        if tokens[j] == "\n":
                            tokens[j] = "}\n"
                            i=j
                            break
            return tokens

        tokens = replace_comments(tokens)

        tokens = ["\\Repeat" if token == "do" else token for token in tokens]
        for i in range(len(tokens)):
            if tokens[i] == "while" and tokens[i-1] == "}" and tokens[i+2] != "{":
                tokens[i] = "\\Until{}"
                tokens[i-1] = ""


        tokens = ["$\gets$" if token == "=" else token for token in tokens]
        tokens = ["\%" if token == "%" else token for token in tokens]
        tokens = ["$\geq$" if token == ">=" else token for token in tokens]
        tokens = ["$\leq$" if token == "<=" else token for token in tokens]
        tokens = ["$\phi$" if token == "null" else token for token in tokens]
        tokens = ["\\State \\Return" if token == "return" else token for token in tokens]
        tokens = ["Input" if token == "cin" else token for token in tokens]
        tokens = ["Output" if token == "cout" else token for token in tokens]

        # print(tokens)


        def convert(tokens: List[str]) -> str:
            stack = []
            a=0
            latex_code1 = ""
            for i, token in enumerate(tokens):
                if token in ['while', 'for', 'if']:
                    condition = tokens[i + 1]
                    condition=condition[1:-1]
                    a=1

                
                    if token == 'while':
                        latex_code1 += f"\\While{{{condition}}}\n"
                        i+=2
                    elif token == 'for':
                        latex_code1 += f"\\For{{{condition}}}\n"
                    elif token == 'if':
                        latex_code1 += f"\\If{{{condition}}}\n"
                        i+=2
                    stack.append((token, i + 2))
                    
                elif token == 'else':
                    if tokens[i + 1] == 'if':
                        a=2
                        condition = tokens[i + 2]
                        condition=condition[1:-1]
                        latex_code1 += f"\\ElsIf{{{condition}}}\n"
                        stack.append(('elseif', i + 3))
                    else:
                        latex_code1 += "\\Else\n"
                        stack.append(('else', i + 1))
                elif token == '}':
                    start = stack[-1][1]
                    flow_control = stack.pop()[0]
                    code_snippet=""
                    
                    if flow_control == 'while':
                        latex_code1 += "\\EndWhile\n"
                    elif flow_control == 'for':
                        latex_code1 += "\\EndFor\n"
                    elif flow_control == 'if':
                        j = i + 1
                        while j < len(tokens) and tokens[j] != 'else':
                            if j<len(tokens) and tokens[j]=='else':
                                break
                            j += 1
                        if j == len(tokens):
                            latex_code1 += "\\EndIf\n"
                    elif flow_control == 'elseif':
                        j = i + 1
                        while j < len(tokens) and tokens[j] != 'else':
                            if j<len(tokens) and tokens[j]=='else':
                                break
                            j += 1
                        if j == len(tokens):
                            latex_code1 += "\\EndIf\n"
                    elif flow_control == 'else':
                        latex_code1 += "\\EndIf\n"

                elif a > 0 :
                    a=a-1  
                else:
                    latex_code1+= tokens[i] +" "
            return latex_code1




        code =convert(tokens)
        latex_code+=code



        latex_code += """\\EndProcedure
        \\end{algorithmic}
        \\end{algorithm}
        \\end{document}
        """

        s = latex_code
        s = re.sub(r">", r"$>$", s)
        s = re.sub(r"<", r"$<$", s)
        s = re.sub(r"<=", r"$\\leq$", s)
        s = re.sub(r">=", r"$\\geq$", s)
        s = re.sub(r"!=", r"$\\neq$", s)
        s = re.sub(r" \\State \\", r"\\", s)
        s = re.sub(r"&&", r"$\&$", s)
        s = re.sub(r"\|\|", r"$\|$", s)

        out = s

    return render_template('index.html', output=out)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug = True)
