import os
import time
from fpdf import FPDF
from datetime import datetime
from flask import Flask, request, render_template,request,make_response
from number import number_bags, result, name, peso_bag,result_bruto,weights,check_box
import importlib
decimal_places = 3

app = Flask(__name__)

@app.route('/save_number', methods=['POST'])
def save_number():
    # Recebe os valores do formulário
    number_bags = request.form['number']
    peso_bag = request.form['peso_bag']
    selected_options = request.form.getlist('time_option')

    # Definir o caminho para o arquivo number.py
    file_path = 'number.py'

    # Mapeamento dos valores das checkboxes
    checkbox_values = {
        'morning': 'Pet',
        'afternoon': 'Pat',
        'evening': 'PP'
    }

    # Criar uma lista para armazenar novas linhas para o arquivo
    new_lines = []

    # Abrir o arquivo para leitura
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Adicionar ou atualizar os valores no conteúdo existente
    found_number_bags = False
    found_peso_bag = False
    existing_checkboxes = set()  # Usar um set para checkboxes existentes

    for line in lines:
        if line.startswith('number_bags ='):
            new_lines.append(f'number_bags = {number_bags}\n')
            found_number_bags = True
        elif line.startswith('peso_bag ='):
            new_lines.append(f'peso_bag = {peso_bag}\n')
            found_peso_bag = True
        elif line.startswith('check_box ='):
            # Extrair o valor do checkbox
            key = line.strip().split('=')[1].strip()
            existing_checkboxes.add(key)
        else:
            new_lines.append(line)

    # Adicionar as novas linhas se não foram encontradas
    if not found_number_bags:
        new_lines.append(f'number_bags = {number_bags}\n')
    if not found_peso_bag:
        new_lines.append(f'peso_bag = {peso_bag}\n')

    # Adicionar ou atualizar os valores das checkboxes
    new_checkboxes = {value for option, value in checkbox_values.items() if option in selected_options}

    # Atualizar linhas com novos checkboxes
    for value in new_checkboxes:
        if value not in existing_checkboxes:
            new_lines.append(f'check_box = "{value}"\n')  # Garantir que os valores são tratados como strings

    # Remover checkboxes que não estão mais selecionados
    new_lines = [line for line in new_lines if not line.startswith('check_box =') or line.strip().split('=')[1].strip().strip('"') in new_checkboxes]

    # Reescrever o arquivo com o conteúdo atualizado
    with open(file_path, 'w') as f:
        f.writelines(new_lines)

    # Renderizar o template com o número de bags
    return render_template('calculo.html', number=int(number_bags))
app.secret_key = 'sua_chave_secreta_aqui'

# Função para ler e atualizar `number_bags`
def get_number_bags():
    import number
    importlib.reload(number)  # Recarregar o módulo para garantir que o valor esteja atualizado
    return number.number_bags

@app.route('/save_weights', methods=['POST'])
def save_weights():
    # Receber o valor de number_bags diretamente do arquivo
    number_bags = get_number_bags()

    weights = []

    print(f"Number of bags (start): {number_bags}")  # Debugging

    for i in range(int(number_bags)):
        weight = request.form.get(f'input{i}')
        if weight:
            weight = weight.replace(',', '.')
            rounded_weight = round(float(weight), decimal_places)
            weights.append(rounded_weight)
    
    print(f"Weights collected: {weights}")  # Debugging

    with open('number.py', 'r') as f:
        lines = f.readlines()
    
    peso_bag = None
    for line in lines:
        if line.startswith('peso_bag ='):
            peso_bag = line.split('=')[1].strip().replace('"', '')
            break

    if peso_bag is None:
        return "Peso da bolsa não definido.", 500

    peso_bag = float(peso_bag)
    soma = sum(weights)
    soma = round(soma, decimal_places)
    total = soma - peso_bag
    total_liquid = round(total, decimal_places)

    with open('number.py', 'w') as f:
        for line in lines:
            if line.startswith('weights ='):
                f.write(f'weights = {weights}\n')
            elif line.startswith('result ='):
                f.write(f'result = {total_liquid}\n')
            elif line.startswith('result_bruto ='):
                f.write(f'result_bruto = {soma}\n')
            else:
                f.write(line)

    return render_template('resultado.html', result_bruto=soma, result_liquid=total_liquid, peso_bag=peso_bag)


@app.route('/save_files', methods=['POST'])
def save_files():
    name = request.form.get('name')

    if not name:
        return "Nome não fornecido.", 400

    # Lê o arquivo 'number.py' e substitui o nome
    with open('number.py', 'r') as f:
        lines = f.readlines()

    with open('number.py', 'w') as f:
        for line in lines:
            if line.startswith('name ='):
                f.write(f'name = "{name}"\n')
            else:
                f.write(line)

    now = datetime.now()
    current_time = now.strftime("%d/%m/%Y %H:%M:%S")
    
    def create_pdf(file_name=None):
        # Lê o arquivo 'number.py'
        with open('number.py', 'r') as f:
            lines = f.readlines()

        # Variáveis para armazenar os valores extraídos
        peso_bag = None
        result_bruto = None
        result = None
        weights = None
        
        # Extrai as variáveis do arquivo 'number.py'
        for line in lines:
            if 'peso_bag' in line:
                peso_bag = line.split('=')[1].strip().replace('"', '')
            elif 'result_bruto' in line:
                result_bruto = line.split('=')[1].strip().replace('"', '')
            elif 'result' in line:
                result = line.split('=')[1].strip().replace('"', '')
            elif 'weights' in line:
                weights = line.split('=')[1].strip().replace('"', '')

        # Importa a função check_box de 'number.py'
        from number import check_box

        # Cria o PDF em memória
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Adiciona o conteúdo ao PDF
        pdf.cell(200, 10, txt=f'{current_time}', ln=True, align='C')
        pdf.cell(200, 10, txt="", ln=True)
        pdf.cell(200, 10, txt=f'{name}', ln=True, align='C')
        pdf.cell(200, 10, txt="", ln=True)
        
        # Processar e formatar a lista de weights
        if weights:
            pdf.cell(200, 10, txt=f"Pesos das Bags:", ln=True, align='L')
            for weight in weights.split(','):  # Supondo que weights seja uma string separada por vírgulas
                try:
                    cleaned_weight = weight.strip().strip('[]').strip()
                    float_weight = float(cleaned_weight)
                    if float_weight > 0:  # Ignora valores zero ou negativos, se necessário
                        formatted_weight = f'{check_box} {float_weight:.1f} kg'
                        pdf.cell(200, 10, txt=formatted_weight, ln=True, align='L')
                except ValueError:
                    continue
        else:
            pdf.cell(200, 10, txt="Nenhum valor de Bag disponível", ln=True, align='C')
        pdf.cell(200, 10, txt=f'Peso da Bag: {peso_bag}kg', ln=True, align='C')
        pdf.cell(200, 10, txt=f'Peso Total bruto: {result_bruto}kg', ln=True, align='C')
        pdf.cell(200, 10, txt=f'Peso Total liquido: {result}kg', ln=True, align='C')

        # Gera o PDF em memória e prepara a resposta HTTP
        response = make_response(pdf.output(dest='S').encode('latin1'))
        response.headers.set('Content-Disposition', 'inline', filename=file_name if file_name else 'documento.pdf')
        response.headers.set('Content-Type', 'application/pdf')

        return response
    
    # Gera o PDF e retorna a resposta
    return create_pdf()

@app.route('/')
def index():
    return render_template('contagem.html')

#@app.route('/enviado')
#def enviado():
    #return render_template('enviado.html', name=name)

@app.route('/resultado')
def resultado():
    return render_template('resultado.html', result=result, name=name)

@app.route('/calculo')
def calculo():
    return render_template('calculo.html', number=number_bags)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80)