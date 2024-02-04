## <b>How to Run Data Cleanser</b>
---
1. Clone this repository
2. Install module needed by inputting this code.
> pip install -r requirements. txt
3. Run the app
> python data-cleanser.py
4. Open browser and go to link below
> http://127.0.0.1:5000/docs/

Successful deployment results below.
<img src="img_md/app.png" alt="alt text" width="whatever" height="whatever"> 

## <center><b>Analysis Report</b></center>
---
### <b>Introduction</b>
<div style="text-align: justify">
Social media is a platform where people can express their opinions freely, including hate speech. Hate speech can be related to politics, racism, religion, and so on. In many cases, hate speech is also often accompanied by the use of abusive words. Apart from creating an unhealthy environment, abusive words themselves often distract from the point of the text. Apart from abusive words, slang words are also often used on social media. In fact, these words can make it difficult for readers to understand the text.

Based on these problems, further analysis is needed regarding text cleaning to make it easier to read as well as analyzing the pattern of tweets in cyberspace, both hate speech and non-hate speech, and how they are characterized.

Therefore, the purpose of this study is to clean the text from abusive words and slang words, identify words related to hate speech, compare hate speech and non-hate speech tweets, and analyze the relationship between hate speech and abusive words.
</div>

### <b>Research Method</b>
#### Dataset Used
<div style="text-align: justify">
Datased used was obtained from ____.

It contained 3 datasets:

- **data.csv**: the inputted dataset. This data will be processed with the application.
- **kamus_alay.csv**:
- **abusive.csv**: 

</div>

#### Data Cleansing
<div style="text-align: justify">
Data cleansing applied in this study includes:

* Removing hashtag
* Removing “USER”, “URL”, and link (https:/….)
* Removing “\n” or enter
* Removing punctuations
* Transforming slang words to normal words
* Censoring abusive words into ****
* Fixing whitespace
</div>

#### Data Analysis Method
<div style="text-align: justify">
The method used is descriptive analytics to find out the condition of the data. Exploratory Data Analysis was also applied. After that, missing values and duplicates were checked and removed (if there was any). Beside that, descriptive statistics were also used to provide a concise overview of the data.
</div>

#### Data Visualization
<div style="text-align: justify">
Data visualization in this study uses:

- Pie chart
- Bar chart
- Wordcloud
</div>

### <b>Results and Conclusion</b>
<div style="text-align: justify">

</div>

### <b>Visualization</b>
<div style="text-align: justify">

#### Pie Chart
##### Comparison of Number of Hate Speech and No Hate Speech Tweets
<img src="img_md/piechart1.png" alt="alt text" width="whatever" height="200"> <img src="img_md/piechart2.png" alt="alt text" width="whatever" height="200"> 

</div>

#### Bar Chart
##### Distribution of

#### Wordcloud
##### Wordcloud of All Tweets


##### Wordcloud of Hate Speech Tweets
<img src="img_md/wordcloud_HS.png" alt="alt text" width="whatever" height="whatever">

##### Wordcloud of Not Hate Speech Tweets
<img src="img_md/wordcloud_no_HS.png" alt="alt text" width="whatever" height="whatever">


---
## <b>Example</b>
### Before Cleansing
### After Cleansing