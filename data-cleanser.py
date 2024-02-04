import re
import string
import pandas as pd
from nltk import word_tokenize
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flasgger import Swagger, swag_from, LazyString, LazyJSONEncoder

app = Flask(__name__)

from sqlalchemy import create_engine
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import requests

class CustomFlaskAppWithEncoder(Flask):
    json_provider_class = LazyJSONEncoder

app = CustomFlaskAppWithEncoder(__name__)

app.json_encoder = LazyJSONEncoder

#------------------------------------------------------------------------------------
# UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
api = Api(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class UploadCSV(Resource):
    @swag_from("docs/csv_upload.yml", methods=["POST"])
    def post(self):
        if 'file' not in request.files:
            return jsonify({'error': 'File tidak ditemukan'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Tidak ada file terpilih'}), 400

        if file and allowed_file(file.filename):
            datasetOri = pd.read_csv(file,encoding='latin-1')
            datasetOri = EDA(datasetOri)
            datasetOri = datasetOri.astype(str)
            output = pd.DataFrame()
            dataset = datasetOri.iloc[:,0]
            dataset = dataset.to_frame(name="Output")

            for column_name in dataset.columns:
                output[column_name] = dataset[column_name].apply(removeHashtag)
                output[column_name] = output[column_name].apply(removeUSERdanURL)
                output[column_name] = output[column_name].apply(removeEnter)
                output[column_name] = output[column_name].apply(removeX)
                output[column_name] = output[column_name].apply(removePunctuation)
                output[column_name] = output[column_name].str.lower()
                output[column_name] = output[column_name].apply(transformSingkatan)
                output[column_name] = output[column_name].apply(removeAbusive2)
                output[column_name] = output[column_name].apply(removeWhitespace)

            print(output)
            output = output.dropna()
            print("".center(100,"-"))
            result_json = output.to_json(orient='records')

            engine = create_engine('sqlite:///output.db', echo=True)
            sqlite_connection = engine.connect()
            sqlite_table = "output_table"
            output.to_sql(sqlite_table, sqlite_connection, if_exists='replace')
            sqlite_connection.close()

            for column_name in output.columns:
                output[column_name] = output[column_name].apply(removeStopword)
                str_output = ' '.join(output[column_name])

            datasetKelas = datasetOri.iloc[:,1:]
            datasetOutput = pd.concat([output, datasetKelas], axis=1)

            perbandinganHS = datasetOutput['HS'].replace({'0': 'Bukan HS', '1': 'HS'})
            hs_counts = perbandinganHS.value_counts()
            # fig, ax = plt.subplots()
            # bars = plt.bar(hs_counts.index, hs_counts.values, color=['green', 'red'])
            # plt.xlabel('Hate Speech (HS)')
            # plt.ylabel('Jumlah')
            # plt.title('Perbandingan Jumlah Cuitan Hate Speech dan Not Hate Speech')

            # for bar in bars:
            #     yval = bar.get_height()
            #     plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom')
            # # plt.imshow()
            fig, ax = plt.subplots(figsize=(10, 8))
            colors = ['green','red']
            wedges, texts, autotexts = ax.pie(hs_counts.values, labels=hs_counts.index, autopct=lambda p: '{:.0f} ({:.1f}%)'.format(p * sum(hs_counts.values) / 100, p), colors=colors, startangle=90)
            for autotext in autotexts:
                autotext.set(color='white', fontweight='bold')
            ax.axis('equal')  
            plt.title('Perbandingan Jumlah Cuitan Hate Speech dan Bukan Hate Speech')
            plt.savefig('image\piechart1.png', format='png')
            plt.close()

            datasetHS = datasetOutput[datasetOutput["HS"] == "1"]
            perbandinganHS = datasetHS['Abusive'].replace({'0': 'Bukan Abusive', '1': 'Abusive'})
            hs_counts = perbandinganHS.value_counts()
            # fig, ax = plt.subplots()
            # bars = plt.bar(hs_counts.index, hs_counts.values, color=['red','green'])
            # plt.xlabel('Hate Speech (HS)')
            # plt.ylabel('Jumlah')
            # plt.title('Perbandingan Jumlah Abusive dan Not Abusive dalam Tipe Hate Speech')

            # for bar in bars:
            #     yval = bar.get_height()
            #     plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom')
            # plt.imshow()
            fig, ax = plt.subplots(figsize=(10, 8))
            colors = ['red', 'green']
            wedges, texts, autotexts = ax.pie(hs_counts.values, labels=hs_counts.index, autopct=lambda p: '{:.0f} ({:.1f}%)'.format(p * sum(hs_counts.values) / 100, p), colors=colors, startangle=90)
            for autotext in autotexts:
                autotext.set(color='white', fontweight='bold')
            ax.axis('equal')  

            plt.title('Perbandingan Jumlah Hate Speech yang Mengandung Kata Abusive dan Bukan Abusive')
            plt.tight_layout()
            plt.savefig('image\piechart2.png', format='png')
            plt.close()

            jumlah_tipe_HS = datasetHS.iloc[:, 3:].apply(pd.to_numeric).sum()
            jumlah_tipe_HS.plot(kind='bar', color='skyblue', figsize=(10, 9))
            plt.xlabel('Tipe Hate Speech')
            plt.ylabel('Jumlah')
            plt.title('Persebaran Tipe Hate Speech')
            plt.tight_layout()
            plt.savefig('image\barchart1.png', format='png')
            plt.close()

            datasetAbusive = datasetOutput[datasetOutput["Abusive"] == "1"]
            jumlah_tipe_Abusive = datasetAbusive.iloc[:, 3:].apply(pd.to_numeric).sum()
            jumlah_tipe_Abusive.plot(kind='bar', color='skyblue', figsize=(10, 9))
            plt.xlabel('Tipe Hate Speech')
            plt.ylabel('Jumlah')
            plt.title('Persebaran Tipe Hate Speech yang Mengandung Kata Abusive')
            plt.tight_layout()
            plt.savefig('image\barchart2.png', format='png')
            plt.close()
            
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(str_output)

            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.savefig('image\wordcloud.png', format='png')
            plt.close()

            feature_columns = list(datasetKelas.columns)
            dataset_no_HS = datasetOutput.loc[datasetOutput['HS'] == '0']
            teks = ' '.join(dataset_no_HS["Output"])
            teks = removePunctuation(teks)
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(teks)

            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.savefig('image\wordcloud_no_HS.png', format='png')
            plt.close()

            nama_file = ["image\piechart1.png", "image\piechart2.png", "image\barchart1.png", "image\barchart2.png", "image\wordcloud.png", "image\wordcloud_no_HS.png"]
            
            for column in feature_columns:
                filtered_output = datasetOutput[datasetOutput[column] == "1"]
                teks = ' '.join(filtered_output["Output"])
                teks = removePunctuation(teks)
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(teks)
                nama = 'image\wordcloud_'+column+".png"
                nama_file.append(nama)
                plt.figure(figsize=(10, 5))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.savefig(nama, format='png')
                plt.close()

            response_data = {
            'status_code': 200,
            'message': 'File berhasil diunggah.',
            'sqlite3_url': '/output.db',
            'list_wordcloud': nama_file,
            'output': result_json
            }
            return jsonify(response_data), 200
        else:
            return jsonify({'error': 'Format file tidak valid'}), 400

app.add_url_rule('/uploadCSV', view_func=UploadCSV.as_view('upload_csv'))
# api.add_resource(UploadCSV, '/uploadCSV')

#------------------------------------------------------------------------------------

swagger_template = dict(
    info = {
        'title': LazyString(lambda:'API Documentation for Data Cleansing'),
        'version': LazyString(lambda:'1.0.0'),
        'description': LazyString(lambda:'Dokumentasi API untuk Data Cleansing')

    },
    host = "127.0.0.1:5000/"
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template,
                  config=swagger_config)

def EDA(dataset):
    print("Exploratory Data Analysis".center(100,"─"))
    print(" Shape Dataset ".center(100,"-"))
    print(dataset.shape)
    print(" Info Dataset ".center(100,"-"))
    print(dataset.info())
    # print(" Deskripsi Dataset ".center(100,"-"))
    # data_desc = dataset.describe()
    # print(data_desc)
    print("".center(100,"─"))
    if dataset.duplicated().any():
        print("Data memiliki nilai duplikat.")
        print("".center(100, "─"))
        dataset = dataset.drop_duplicates()
        print("Shape dataset setelah menghapus duplikat adalah",dataset.shape)
        # print(" Deskripsi Dataset Setelah Menghapus Duplikat ".center(100, "-"))
        # print(dataset.describe())
    else:
        print("Data tidak memiliki nilai duplikat.")
    print("".center(100,"─"))
    print(" Mengecek Missing Value ".center(100,"─"))
    total_nan = dataset.isna().sum()
    print(total_nan)
    print("".center(100,"─"))
    if total_nan.all()==0:
        print("Data tidak memiliki missing value.")
    else:
        print("Data memiliki missing value.")
        dataset = dataset.dropna()
    print("".center(100,"─"))
    print(dataset.iloc[:,1:].corr())
    print("".center(100,"─"))
    return(dataset)

def removeHashtag(teks):
    output = re.sub(r'#\w+', ' ', teks)
    return output

def removeUSERdanURL(teks):
    output = re.sub('USER', ' ', teks)
    output = re.sub('URL', ' ', output)
    output = re.sub('RT', ' ', output)
    output = re.sub(r'http\S+', ' ', output) 
    output = re.sub('&amp;', ' ', output)
    return output

def removeEnter(teks):
    output = re.sub(r'\n', ' ', teks)
    output = re.sub(r'\\u', ' ', output)
    return output

def removeX(teks):
    # output = re.sub(r'\b[x]\w{2}\b', ' ', teks)
    output = re.sub(r'\s*\\xa\w*\s*', ' ', teks)
    output = re.sub(r'xd', ' ', output)
    return output

def removePunctuation(teks):
    punctuation = string.punctuation
    output = ''.join(char if char not in punctuation else ' ' for char in teks)
    output = re.sub(r'[^a-zA-Z0-9\s]', ' ', output) #remove simbol aneh2
    output = re.sub(r'\b[x]\w{2}\b', ' ', output)
    return output

def removeWhitespace(teks):
    output = ' '.join(teks.split())
    return output

def transformSingkatan(teks):
    # tokens = word_tokenize(teks)
    data_singkatan = pd.read_csv(r'data\new_kamusalay.csv', encoding='latin-1', header=None)
    data_singkatan.columns = ['Singkatan', 'Normal']
    dictSingkatan = dict(zip(data_singkatan['Singkatan'], data_singkatan['Normal']))

    output = ' '.join(dictSingkatan.get(word, word) for word in teks.split()) #atau tokens
    return output

# agaknya maksa
def removeAbusive2(teks):
    data_abusive = pd.read_csv(r'data\abusive.csv')
    list_data_abusive = list(data_abusive['ABUSIVE'])
    output = []
    tokens = word_tokenize(teks)

    i = 0
    for word in tokens:
        for i in range (0,len(list_data_abusive)):
            if word.lower()==list_data_abusive[i]:
                word = re.sub(list_data_abusive[i], "*"*len(word), word.lower())
            i = i+1
        output.append(word)
    return ' '.join(output)
        
def removeStopword(teks):
    stopword_factory = StopWordRemoverFactory()
    stopword_list = stopword_factory.get_stop_words()
    # latest_stopwords = get_latest_stopwords()
    latest_stopwords = ['entah', 'tutur', 'sebuah', 'menuju', 'tadinya', 'nyaris', 'beginikah', 'sampaikan', 'menandaskan', 'berkehendak', 'kelihatan', 'nanti', 'ucapnya', 'sebagai', 'antaranya', 'padahal', 'apaan', 'menyebutkan', 'seringnya', 'berikutnya', 'tampaknya', 'ok', 'sini', 'aku', 'berarti', 'bertanya-tanya', 'selalu', 'kedua', 'setibanya', 'dimulainya', 'ungkapnya', 'jelaskan', 'mengenai', 'diperlukannya', 'penting', 'sekalipun', 'diperlukan', 'sepanjang', 'sendirinya', 'berturut', 'selama', 'secara', 'mula', 'iya', 'tinggi', 'meskipun', 'buat', 'gunakan', 'terjadilah', 'sekadarnya', 'ditegaskan', 'keseluruhannya', 'tiba-tiba', 'paling', 'sinilah', 'para', 'diminta', 'biasanya', 'mampu', 'semasa', 'ibarat', 'berapapun', 'bermaksud', 'seolah-olah', 'diberi', 'adapun', 'mirip', 'bermula', 'menaiki', 'makin', 'sesama', 'kecuali', 'sendirian', 'selamanya', 'bertanya', 'bakal', 'bulan', 'menyeluruh', 'segera', 'dimulailah', 'asalkan', 'sejak', 'mendapat', 'sejumlah', 'umumnya', 'ditandaskan', 'lanjut', 'sama-sama', 'bukannya', 'ingat-ingat', 'sebagainya', 'jelaslah', 'kelamaan', 'memberi', 'ibaratkan', 'mari', 'entahlah', 'masa', 'meyakini', 'nih', 'dikira', 'tanyanya', 'percuma', 'berjumlah', 'akhirnya', 'seterusnya', 'semasih', 'terlebih', 'dsb', 'pun', 'mengungkapkan', 'siap', 'cukuplah', 'adanya', 'kembali', 'memisalkan', 'awalnya', 'luar', 'enggak', 'bertutur', 'sesekali', 'sebagaimana', 'pada', 'ditambahkan', 'dalam', 'hingga', 'beginilah', 'pertanyakan', 'menanti-nanti', 'inginkah', 'kapankah', 'sewaktu', 'soalnya', 'sepertinya', 'mereka', 'dst', 'anda', 'makanya', 'panjang', 'sekitarnya', 'ada', 'hari', 'banyak', 'beginian', 'secukupnya', 'semula', 'belakang', 'ditunjuk', 'andalah', 'akulah', 'berlangsung', 'betulkah', 'kebetulan', 'tegasnya', 'mengibaratkan', 'mendatangkan', 'harusnya', 'olehnya', 'bila', 'meminta', 'sama', 'kemudian', 'nah', 'dini', 'melalui', 'kira-kira', 'kepadanya', 'biasa', 'memperkirakan', 'waktu', 'perlu', 'datang', 'nantinya', 'kini', 'sebutlah', 'terdahulu', 'setengah', 'mulai', 'rasa', 'demikian', 'waktunya', 'bermacam', 'sebabnya', 'namun', 'saatnya', 'mengatakan', 'sehingga', 'satu', 'keseluruhan', 'dengan', 'memintakan', 'menegaskan', 'berlebihan', 'mengingatkan', 'sepantasnya', 'cukup', 'tanpa', 'katakanlah', 'naik', 'bahkan', 'jauh', 'ketika', 'mungkinkah', 'ku', 'dari', 'bagian', 'seenaknya', 'diketahuinya', 'sebutnya', 'diibaratkan', 'seluruhnya', 'se', 'dikatakan', 'hendaknya', 'sementara', 'jelasnya', 'misal', 'menyangkut', 'hampir', 'segala', 'lima', 'berkeinginan', 'sebab', 'siapakah', 'mengetahui', 'sekalian', 'tersebutlah', 'terasa', 'perlukah', 'kinilah', 'disinilah', 'untuk', 'ditanyakan', 'tambahnya', 'kecil', 'lamanya', 'kenapa', 'terlihat', 'adalah', 'sedangkan', 'dimaksudnya', 'sesudahnya', 'saja', 'hendaklah', 'sangatlah', 'akankah', 'tentulah', 'di', 'sering', 'rasanya', 'amp', 'bermacam-macam', 'masih', 'sejenak', 'ialah', 'sedemikian', 'terus', 'yakin', 'umum', 'maka', 'lebih', 'bersiap', 'apalagi', 'begini', 'malah', 'tiba', 'tempat', 'berupa', 'benarlah', 'yang', 'manakala', 'seraya', 'demikianlah', 'disebut', 'diakhiri', 'jawabnya', 'dibuatnya', 'turut', 'kelima', 'sebaiknya', 'mengerjakan', 'tandas', 'melihatnya', 'bekerja', 'memperlihatkan', 'diantaranya', 'enggaknya', 'kala', 'terdiri', 'rt', 'kalaulah', 'seorang', 'diri', 'kelihatannya', 'baik', 'kah', 'kita', 'mengucapkannya', 'merekalah', 'keinginan', 'terhadapnya', 'inginkan', 'semata-mata', 'termasuk', 'disini', 'apakah', 'tapi', 'pastilah', 'disampaikan', 'ibaratnya', 'belumlah', 'terhadap', 'begitu', 'diucapkannya', 'baru', 'ataupun', 'bersiap-siap', 'memperbuat', 'tambah', 'memihak', 'lain', 'semua', 'lainnya', 'begitupun', 'sekali-kali', 'sayalah', 'berkenaan', 'diberikan', 'kesampaian', 'ujar', 'amat', 'semaunya', 'sedikitnya', 'ibu', 'seolah', 'akan', 'seperti', 'tertuju', 'keadaan', 'berapa', 'dimana', 'diingat', 'kata', 'dikerjakan', 'agak', 'dimaksud', 'diketahui', 'supaya', 'sekaligus', 'siapa', 'hendak', 'berikan', 'bakalan', 'lama', 'kamu', 'sekarang', 'caranya', 'sebegini', 'mengucapkan', 'tandasnya', 'kurang', 'misalnya', 'berakhirnya', 'itukah', 'membuat', 'bagai', 'kamilah', 'sekitar', 'wahai', 'melakukan', 'tepat', 'menurut', 'berawal', 'bersama-sama', 'apa', 'ditunjuknya', 'ucap', 'seusai', 'didatangkan', 'terutama', 'terjadi', 'demi', 'kira', 'ujarnya', 'dimintai', 'masalahnya', 'wkwk', 'bukanlah', 'cara', 'sepantasnyalah', 'tersebut', 'nyatanya', 'sebegitu', 'janganlah', 'dijawab', 'menjelaskan', 'guna', 'pak', 'tersampaikan', 'dapat', 'empat', 'beberapa', 'meski', 'sangat', 'bagaikan', 'beri', 'ditanya', 'diperkirakan', 'dimaksudkan', 'besar', 'mendatang', 'tetap', 'asal', 'berturut-turut', 'antar', 'bagaimanapun', 'memberikan', 'bung', 'mempertanyakan', 'dan', 'khususnya', 'dijelaskan', 'yakni', 'pula', 'tentunya', 'pasti', 'malahan', 'jelas', 'tanyakan', 'usah', 'mendapatkan', 'semuanya', 'berlainan', 'berbagai', 'balik', 'tidaklah', 'disebutkan', 'seberapa', 'memastikan', 'dulu', 'ditunjuki', 'semampu', 'sedang', 'atas', 'menyatakan', 'terakhir', 'deh', 'terlalu', 'toh', 'seharusnya', 'sempat', 'amatlah', 'kami', 'kalau', 'tiga', 'setidak-tidaknya', 'apabila', 'tuturnya', 'tiap', 'diperbuat', 'hanya', 'walau', 'jika', 'apatah', 'inikah', 'tetapi', 'menjadi', 'segalanya', 'keduanya', 'ingin', 'begitukah', 'cukupkah', 'pantas', 'mau', 'semata', 'setempat', 'wong', 'selagi', 'serta', 'menjawab', 'belum', 'bahwa', 'akhiri', 'tertentu', 'dipersoalkan', 'begitulah', 'menghendaki', 'setidaknya', 'diibaratkannya', 'sesampai', 'yaitu', 'sebetulnya', 'jawaban', 'katakan', 'mulailah', 'itu', 'berujar', 'sih', 'dirinya', 'rupanya', 'terdapat', 'tadi', 'menanyai', 'menginginkan', 'mulanya', 'setiba', 'sebelum', 'menyiapkan', 'sesaat', 'dimisalkan', 'pernah', 'ternyata', 'karena', 'itulah', 'ini', 'kamulah', 'menantikan', 'benarkah', 'dialah', 'jadi', 'digunakan', 'kitalah', 'semampunya', 'ataukah', 'lalu', 'selanjutnya', 'bukan', 'sesegera', 'artinya', 'kasus', 'sebisanya', 'jumlah', 'jikalau', 'diungkapkan', 'terbanyak', 'kepada', 'misalkan', 'bukankah', 'daripada', 'diberikannya', 'bolehlah', 'ditunjukkan', 'lanjutnya', 'dikatakannya', 'sebaik-baiknya', 'keterlaluan', 'setelah', 'mengibaratkannya', 'berlalu', 'masihkah', 'pihaknya', 'dulunya', 'kemana', 'sana', 'mengapa', 'kalian', 'dia', 'diantara', 'berapakah', 'menanya', 'dahulu', 'harus', 'saat', 'menambahkan', 'sekadar', 'punya', 'persoalan', 'pertama', 'bilakah', 'kalaupun', 'lagi', 'sesuatunya', 'dimungkinkan', 'soal', 'diingatkan', 'sebaik', 'maupun', 'pihak', 'sela', 'tampak', 'diucapkan', 'ungkap', 'sekiranya', 'nggak', 'meyakinkan', 'dipunyai', 'serupa', 'sudah', 'setiap', 'tegas', 'bisa', 'pertanyaan', 'bawah', 'jumlahnya', 'kemungkinan', 'oleh', 'memang', 'oh', 'tanya', 'dipertanyakan', 'bisakah', 'dong', 'sebelumnya', 'bersama', 'boleh', 'mempunyai', 'mempersoalkan', 'berakhir', 'memerlukan', 'juga', 'justru', 'depan', 'memungkinkan', 'mengatakannya', 'cuma', 'sampai', 'terkira', 'atau', 'selain', 'tolong', 'sepihak', 'dituturkannya', 'menggunakan', 'sebaliknya', 'lah', 'sekurang-kurangnya', 'teringat-ingat', 'seketika', 'berdatangan', 'mempersiapkan', 'bagi', 'sejauh', 'macam', 'antara', 'mempergunakan', 'minta', 'ya', 'sajalah', 'selaku', 'merasa', 'bolehkah', 'melainkan', 'menunjuki', 'dilakukan', 'sebesar', 'sebanyak', 'tunjuk', 'awal', 'dimulai', 'jangankan', 'menanyakan', 'mana', 'berkali-kali', 'wah', 'kan', 'menunjukkan', 'menyampaikan', 'dua', 'pukul', 'rata', 'sendiri', 'masing', 'setinggi', 'benar', 'sebut', 'pertama-tama', 'diperbuatnya', 'mengira', 'tengah', 'seluruh', 'ingat', 'telah', 'karenanya', 'bagaimana', 'seseorang', 'bagaimanakah', 'semacam', 'haruslah', 'dijelaskannya', 'berkata', 'katanya', 'mendatangi', 'tentang', 'ke', 'sekurangnya', 'saling', 'dibuat', 'kapan', 'kok', 'tahu', 'pentingnya', 'agar', 'dilihat', 'banget', 'diperlihatkan', 'tidak', 'jawab', 'manalagi', 'dll', 'ditanyai', 'padanya', 'waduh', 'inilah', 'dekat', 'mampukah', 'jadinya', 'per', 'perlunya', 'dimaksudkannya', 'masing-masing', 'seperlunya', 'sebenarnya', 'masalah', 'diinginkan', 'menunjuknya', 'ikut', 'tidakkah', 'siapapun', 'dikarenakan', 'semisal', 'sekali', 'berakhirlah', 'suatu', 'berapalah', 'menanti', 'tak', 'sebagian', 'sudahlah', 'semakin', 'tentu', 'diakhirinya', 'seingat', 'mungkin', 'selama-lamanya', 'disebutkannya', 'melihat', 'jangan', 'teringat', 'jadilah', 'berada', 'akhir', 'nya', 'mengingat', 'walaupun', 'berikut', 'terjadinya', 'gue', 'dipergunakan', 'sampai-sampai', 'merupakan', 'sesudah', 'keluar', 'dipastikan', 'mengakhiri', 'agaknya', 'kemungkinannya', 'semisalnya', 'ditujukan', 'belakangan', 'dilalui', 'kiranya', 'hanyalah', 'ditunjukkannya', 'usai', 'sesuatu', 'bahwasanya', 'lewat', 'sambil', 'ia', 'didapat', 'haha', 'anu', 'menuturkan', 'betul', 'kapanpun', 'sudahkah', 'sedikit', 'memulai', 'tahun', 'lagian', 'bapak', 'menunjuk', 'dituturkan', 'saya', 'hal', 'sekecil']
    stopword_manual = ['gue','nih','sih','nya','wkwk','iya','deh','nya','ku','rt', 'haha','banget','kayak','eh','ah','aduh','ayo','oi','biar', 'md3']
    stopwords_id = latest_stopwords+stopword_list+stopword_manual
    stopwords_id = list(set(stopwords_id))

    words = teks.split()
    output = [word for word in words if word.lower() not in stopwords_id]
    return ' '.join(output)

@swag_from("docs/text_processing.yml", methods=["POST"])
@app.route('/inputForm',methods=['POST'])
def main_data_cleaning():
    teks = request.form.get('teks')
    teks = removeHashtag(teks)
    teks = removeUSERdanURL(teks)
    teks = removeEnter(teks)
    teks = teks.lower()
    teks = removeX(teks)
    teks = removePunctuation(teks)
    teks = transformSingkatan(teks)
    teks = removeAbusive2(teks)
    teks = removeWhitespace(teks)

    json_response={
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': teks
    }

    response_data = jsonify(json_response)
    return response_data

if __name__ == '__main__':
    app.run() #debug=True