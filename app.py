from flask import Flask,jsonify, render_template,request
from collections import defaultdict
import json
import openai
import pandas as pd
app = Flask(__name__)
openai.api_key = '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'

@app.route('/')
def hello_world():  # put application's code here
    return render_template('base.html')

@app.route('/questions/api',methods=['get'])
def get_questions():
    questions = read_csv('static/题库.csv')
    print(questions)
    return jsonify(questions)
@app.route('/questions/api/<num>',methods=['get'])
def get_question(num):
    questions = pd.read_csv('static/题库.csv')
    if '_' in num:
        num_list = num.split('_')
        num_list = [str(i).strip() for i in num_list if i]
        question = questions[questions['序号'].astype(str).isin(num_list)]
    else:
        question = questions[questions['序号'].astype(str)== str(num)]
    question['选项'] = question['选项'].map(lambda x:json.dumps([i.strip() for i in x.split(r'\n')]))
    question = question.reset_index()
    return question.T.to_json()

@app.route('/ai/api',methods = ['post'])
def ai_helper():
    text = request.data
    text = json.loads(text)
    created = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'study helper', 'content': text}],
        max_tokens=1000,
    )
    return jsonify(created)

def read_csv(csv_file):
    json_res = defaultdict(dict)
    with open(csv_file) as f:
        heads = f.readline().split(',')
        for line in f.readlines()[:]:
            content =line.split(',')
            num = int(content[0])
            for head,content in zip(heads,content):
                json_res[num][head.strip()] = content.strip()
                if head == '选项' and r'\n' in content:
                    json_res[num][head] = [i.strip() for i in content.split(r'\n')]

    return json_res



if __name__ == '__main__':
    app.run()
