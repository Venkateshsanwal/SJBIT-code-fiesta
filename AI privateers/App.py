import streamlit as st
import nltk
import spacy
nltk.download('stopwords')
spacy.load('en_core_web_sm')

import pandas as pd
import base64, random
import time, datetime

from pyresparser import ResumeParser

# from pdfminer3.layout import LAParams, LTTextBox
# from pdfminer3.pdfpage import PDFPage
# from pdfminer3.pdfinterp import PDFResourceManager
# from pdfminer3.pdfinterp import PDFPageInterpreter
# from pdfminer3.converter import TextConverter

from pdfminer.layout import LAParams, LTTextBox
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter


import io, random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import pafy
import plotly.express as px
import youtube_dl

def fetch_yt_video(link):
    video = pafy.new(link)
    return video.title


def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


connection = pymysql.connect(host='localhost', user='root', password='')
cursor = connection.cursor()


def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
    name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills,
    courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


st.set_page_config(
    page_title="AI Privateers Resume Shortlister",
    #page_icon='./Logo/SRA_Logo.ico',
)
#for deleting
def delete_row(row_id):
    delete_sql = f"DELETE FROM user_data WHERE ID = {row_id};"
    cursor.execute(delete_sql)
    connection.commit()

def run():
    st.title("AI Privateers Resume Shortlister")
    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    # img = Image.open('./Logo/SRA_Logo.jpg')
    # img = img.resize((250, 250))
    # st.image(img)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)
    connection.select_db("sra")

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)

    # #DELETE BUTTON
    # cursor.execute('''SELECT * FROM user_data''')
    # data = cursor.fetchall()
    # df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
    #                                  'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
    #                                  'Recommended Course'])

    # # Display the DataFrame
    # st.dataframe(df)

    # # Add UI elements for deletion
    # st.subheader("**Delete Data**")
    # try:
    #     row_id_to_delete = st.number_input("Enter the ID of the row to delete:", min_value=0, max_value=df.shape[0]-1, value=0)
    #     if st.button("Delete Row"):
    #         delete_row(row_id_to_delete)
    #         st.success(f"Row with ID {row_id_to_delete} deleted successfully!")
    # except:
    #     st.write("No data found!!")

    # Add a delete button for each row
    # if st.checkbox("Show Delete Buttons", key='show_delete_buttons'):
    #     for index, row in df.iterrows():
    #         if st.button(f"Delete Row {row['ID']}"):
    #             delete_row(row['ID'])
    #             st.success(f"Row with ID {row['ID']} deleted successfully!")

    if choice == 'Normal User':
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smart recommendation based on it."</h4>''',
        #             unsafe_allow_html=True)
        # jd_file = st.file_uploader("Job Description ", type=["pdf"])
        st.markdown('''JOB DESCRIPTION:\n
BioSymphony Pvt. Ltd. is a trailblazing computational research company dedicated to advancing scientific innovation in the fields of computational biology and drug discovery. Our mission is to develop cutting-edge tools and technologies that empower researchers and scientists to make transformative contributions to their work. We thrive on a collaborative and creative company culture, pushing the boundaries of scientific discovery.


In this role, you will have the opportunity to work on challenging projects that will enhance your programming skills. This internship offers a chance to learn from experienced professionals, gain hands-on experience, and contribute to projects that align with BioSymphony's mission.


Your role:

Collaborate with our development team to understand project requirements and goals.
Assist in designing, coding, testing, and deploying Python-based applications.
Learn about prompt engineering and the utilization of large language models (LLMs) for application enhancement.
Participate in code reviews, discussions, and knowledge-sharing sessions.
Work closely with mentors to enhance your programming skills.


Expectations:

Proficiency in Python programming.
Familiarity with version control systems (e.g., Git).
Knowledge in developing and deploying machine learning models.
Proficiency in programming languages such as Python or R.
Knowledge of machine learning libraries and frameworks (e.g., TensorFlow, PyTorch).
Familiarity with data preprocessing, feature engineering, and model evaluation techniques.
Strong problem-solving skills and attention to detail.
Curiosity and eagerness to learn about prompt engineering and LLMs.
Good communication and teamwork abilities.

If you're passionate about applying your skills to drive scientific innovation, we invite you to apply.

Join us at BioSymphony and contribute to revolutionizing the field of computational biology and drug discovery through innovative machine-learning solutions!''')
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                # if resume_data['no_of_pages'] == 1:
                #     cand_level = "Fresher"
                #     st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',
                #                 unsafe_allow_html=True)
                # elif resume_data['no_of_pages'] == 2:
                #     cand_level = "Intermediate"
                #     st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                #                 unsafe_allow_html=True)
                # elif resume_data['no_of_pages'] >= 3:
                #     cand_level = "Experienced"
                #     st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                #                 unsafe_allow_html=True)

                # st.subheader("**Skills Recommendation💡**")
                ## Skill shows
                keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=resume_data['skills'], key='1')

                ##  recommendation
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']

               

                
                ## Resume writing video
                # st.header("**Bonus Video for Resume Writing Tips💡**")
                # resume_vid = random.choice(resume_videos)
                # res_vid_title = fetch_yt_video(resume_vid)
                # st.subheader("✅ **" + res_vid_title + "**")
                # st.video(resume_vid)

                # ## Interview Preparation Video
                # st.header("**Bonus Video for Interview👨‍💼 Tips💡**")
                # interview_vid = random.choice(interview_videos)
                # int_vid_title = fetch_yt_video(interview_vid)
                # st.subheader("✅ **" + int_vid_title + "**")
                # st.video(interview_vid)

                connection.commit()
            else:
                st.error('Something went wrong..')
    else:
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'ai' and ad_password == 'ai':
                st.success("Welcome Admin")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

                #DELETE BUTTON
                cursor.execute('''SELECT * FROM user_data''')
                data = cursor.fetchall()
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                'Recommended Course'])

                # Display the DataFrame
                st.dataframe(df)

                # Add UI elements for deletion
                st.subheader("**Delete Data**")
                try:
                    row_id_to_delete = st.number_input("Enter the ID of the row to delete:", min_value=0, max_value=df.shape[0]-1, value=0)
                    if st.button("Delete Row"):
                        delete_row(row_id_to_delete)
                        st.success(f"Row with ID {row_id_to_delete} deleted successfully!")
                except:
                    st.write("No data found!!")

                # ## Pie chart for predicted field recommendations
                # labels = plot_data.Predicted_Field.unique()
                # print(labels)
                # values = plot_data.Predicted_Field.value_counts()
                # print(values)
                # st.subheader("📈 **Pie-Chart for Predicted Field Recommendations**")
                # fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills')
                # st.plotly_chart(fig)

                # ### Pie chart for User's👨‍💻 Experienced Level
                # labels = plot_data.User_level.unique()
                # values = plot_data.User_level.value_counts()
                # st.subheader("📈 ** Pie-Chart for User's👨‍💻 Experienced Level**")
                # fig = px.pie(df, values=values, names=labels, title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                # st.plotly_chart(fig)


            else:
                st.error("Wrong ID & Password Provided")


run()
