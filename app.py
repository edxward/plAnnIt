
import os, json, ast, csv, io
from flask import Flask, abort, render_template, url_for, request, send_from_directory, Response
from livereload import Server
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

JSON_DIRECTORY = 'tables'

class timetable_storage:
    def __init__(self):
        self.timetables = {}
        self.tableresults = {}
    def no_of_timetables(self):
        return len(self.timetables)
    def append_timetable(self, data):
        self.timetables[str(self.no_of_timetables()+1)] = data
    def append_result(self, key, result):
        if not result.startswith('[['):
            result = "["+result      # formatting due to inconsistency from AI
        if not result.endswith(']]'):
            result = result+"]"
        if result.startswith('[```plaintext'):
            result = result[13:]
        if result.endswith('```]'):
            result = result[:-4]

        result = max(result.split('`'), key=len)
        self.tableresults[str(key)] = result
    def return_result(self, key):
        return self.tableresults[str(key)]
    def return_timetable(self, id):
        return self.timetables[str(id)]

class sample_data:
    # Example input data
    school_timetable = ["08:00", "14:30", "09:00", "12:30"]

    set_time_activities = {
        "Football Practice": ["15:00", "16:30", "Sporting", 6, "Monday"],
        "Guitar Lesson": ["17:00", "18:00", "Lesson", 4, "Tuesday"],
        "Spanish Tutoring": ["18:30", "19:30", "Academic", 5, "Wednesday"],
        "Karate Class": ["16:00", "17:30", "Sporting", 5, "Thursday"]
    }

    home_activities = {
        "Biology Project Part 1": ["Academic", "01:00", 7],
        "Biology Project Part 2": ["Academic", "01:00", 7],
        "Biology Project Part 3": ["Academic", "01:00", 7],
        "Maths Homework": ["Academic", "00:45", 5],
        "History Essay Part 1": ["Academic", "01:30", 8],
        "History Essay Part 2": ["Academic", "01:30", 8],
        "Art Portfolio Work Part 1": ["Other", "01:00", 4],
        "Art Portfolio Work Part 2": ["Other", "01:00", 4],
        "Gaming Session with Friends": ["Other", "01:30", 3],
        "Meditation and Relaxation": ["Other", "00:30", 1]
    }

    # Crammed Schedule: Test Burnout Score 
    class crammed:
        school_timetable = ["07:30", "15:30", "08:30", "13:30"]

        set_time_activities = {
            "Football Practice": ["16:00", "17:30", "Sporting", 6, "Monday"],
            "Piano Lesson": ["18:00", "19:00", "Lesson", 4, "Monday"],
            "Basketball Training": ["16:30", "18:00", "Sporting", 7, "Tuesday"],
            "Math Tutoring": ["18:30", "20:00", "Academic", 8, "Tuesday"],
            "Science Club": ["16:00", "17:30", "Academic", 5, "Wednesday"],
            "Karate Class": ["18:00", "19:30", "Sporting", 6, "Wednesday"],
            "Art Workshop": ["15:45", "17:15", "Other", 4, "Thursday"],
            "Spanish Tutoring": ["17:30", "18:30", "Academic", 5, "Thursday"],
            "Swimming Practice": ["09:00", "11:00", "Sporting", 7, "Saturday"],
            "Photography Club": ["11:30", "13:00", "Other", 3, "Saturday"]
        }

        home_activities = {
            "Biology Project Part 1": ["Academic", "01:00", 7],
            "Biology Project Part 2": ["Academic", "01:00", 7],
            "Biology Project Part 3": ["Academic", "01:00", 7],
            "History Essay Part 1": ["Academic", "01:30", 8],
            "History Essay Part 2": ["Academic", "01:30", 8],
            "GCSE Maths Revision Part 1": ["Academic", "01:00", 9],
            "GCSE Maths Revision Part 2": ["Academic", "01:00", 9],
            "GCSE Science Revision Part 1": ["Academic", "01:00", 8],
            "GCSE Science Revision Part 2": ["Academic", "01:00", 8],
            "Art Portfolio Work Part 1": ["Other", "01:00", 4],
            "Art Portfolio Work Part 2": ["Other", "01:00", 4],
            "Gaming Session with Friends": ["Other", "01:30", 3],
            "Relaxation and Meditation": ["Other", "00:30", 1],
            "Organizing Desk": ["Other", "00:45", 2],
            "Household Chores": ["Other", "01:00", 3]
        }

    # Light schedule: Test Burnout Score
    class light:
        school_timetable = ["08:00", "14:30", "09:00", "12:30"]

        set_time_activities = {
            "Football Practice": ["15:30", "16:30", "Sporting", 4, "Monday"],
            "Guitar Lesson": ["17:00", "17:45", "Lesson", 3, "Tuesday"],
            "Spanish Tutoring": ["18:00", "18:45", "Academic", 3, "Wednesday"],
            "Karate Class": ["16:30", "17:15", "Sporting", 3, "Thursday"]
        }

        home_activities = {
            "Biology Project": ["Academic", "01:00", 6],
            "Maths Homework": ["Academic", "00:30", 4],
            "History Essay": ["Academic", "01:00", 6],
            "Art Portfolio Work": ["Other", "00:45", 3],
            "Gaming Session with Friends": ["Other", "01:00", 2],
            "Meditation and Relaxation": ["Other", "00:30", 1]
        }




api_key = os.getenv("OPENAI_API_KEY")
DB = timetable_storage()

class OPENAI_INSTANCE:
    def __init__(self, OPENAI_KEY):
        self.api_key = OPENAI_KEY

    def test_call(self):
        return self.openai_call("Repeat after me: '123'")
    
    def db_routine(self, db_key):
        result_routine = self.openai_call(self.create_prompt(DB.return_timetable(db_key)[0],DB.return_timetable(db_key)[1],DB.return_timetable(db_key)[2]))
        DB.append_result(db_key,result_routine)
        
    def fix_json(self, json):
        json_fix_prompt = """fix this python list. do not add any text before or after and do not modify the data within. Do not beautify it, you only need to return it in one line. 

        The list should contain 2 items. ensure there are no missing commas, unclosed brackets, etc etc 

        It should look like this:   [[data, int] , [data, int]]
        
        Data: {}""".format(json)

        return self.openai_call(json_fix_prompt)
    
    def timetable_check(self, json):
        timetable_check_prompt = """here is a python list containing 2 different timetables. Your job is to go through, ensure that there are no repeated activities throughout the week EXCEPT SCHOOL .

        Each activity should only appear ONCE on each of the timetables. If it appears on multiple days in the same timetable, only keep the one on the day with the least number of other activities.
        ENSURE THAT ALL ACTIVITIES APPEAR ONCE ON EACH TIMETABLE. DO NOT DELETE ALL INSTANCES OF AN ACTIVITY, ENSURE THAT ONLY 1 IS KEPT.
        DO NOT ADD ANY EXTRA TEXT BEFORE OR AFTER. RETURN THE LIST IN PLAIN TEXT.
        
        Data: {}""".format(json)

        return self.openai_call(timetable_check_prompt)
    
    def openai_call(self, prompt):
        
        client = OpenAI(api_key=self.api_key)

        MODEL = "o1-mini"

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )

        answer = (response.choices[0].message.content)
        return answer
    def create_prompt(self, school_timetable, set_time_activities, home_activities):
        """
        set_time_activities: {name:[start_time,finish_time,type,stressfulness,day], ....}
        school_activities: [start_time,finish_time,friday_start,friday_finish]
        home_activities: {name:[type,est_time,stressfulness], ....}

        As the result will be directly processed by code, we will ask chatgpt to return it as JSON
        """

        prompt_part1 = """You are going to create a timetable with the express purpose of reducing burnout and managing stress. 
        To do this, you will be provided with my school timetable (The timings are the same Monday-Thursday but may be different on Friday)
        Then, you will be provided with my fixed-timing activities and my non-fixed-timing activities.\n\n"""

        prompt_part2 = """Now, I will give you my school timetable in the following format: [start_time,finish_time,friday_start,friday_finish]. There is no school on Sat/Sun.
        start_time and finish_time refer to the start and end of school on Monday-Thursday, friday_start and friday_finish refer to the start and end on friday.
        Data: {}\n\n""".format(str(school_timetable))

        prompt_part3 = """Now, I will give you my set-time activities in the following format: {name:[start_time,finish_time,type,stressfulness,day], ....}
        This is a python dictionary format. Name=The name of the set-time activity, start_time and finish_time are the timings, type is either Academic, Sporting, Lesson (e.g. piano or tutoring) or other.
        Stressfulness is a scale of 1-10 on how stressful I find this activity. Keep in mind that some activities, e.g. sporting ones like rugby may cause more burnout that other activities such as a piano lesson.
        The day of these lessons cannot be changed.
        Data: """+str(set_time_activities)+"\n\n"

        prompt_part4 = """Now, I will give you my non set-time activities, such as homework, revision, etc. This is in the following format: {name:[type,est_time,stressfulness], ....}
        This is a python dictionary format. Name=The name of the non set-time activity, est_time is the estimated time, stressfulness is a scale of 1-10 on how stressful I finde this activity.
        EACH ACTIVITY MUST APPEAR EXACTLY AND ONLY ONCE ON EACH TIMETABLE. DO NOT DISOBEY THIS INSTRUCTION
        Data: """+str(home_activities)+"\n\n"

        prompt_part5 = """
        
        This data should be returned strictly in the following format: [[{day:[{item: [startTime,finishTime]}, ...], ... },burnout_score] , [{day:[{item: [startTime,finishTime]}, ...], ... },burnout_score]]
        This is a list with two items inside, one for each timetable. Each timetable is also a list, containing the timetable and burnout score. The timetable is a dictionary
        with an entry for each day.

        To create this timetable do the following:
        1. Create each day (mon-sun) with an empty list of items
        2. Add my school timings to the applicable days
        3. Add my set-time activities to the correct date and time (each set-time activity should only appear once and on the correct day and time)
        4. Organise my non set-time activities into the timetable using the following method:

        Your job is to organise my non set-time activities in the time between school and set-time activities in such a way to reduce too much stress in any one day in order to reduce burnout. You can do this by looking at the stressfulness scales provided with each activity.
        factor in the the amount of downtime, especially on weekdays, the number of days with multiple high-stress activities, etc.
        Keep in mind that school can add some stress, especially on the longer Monday-Thursday days, and having multiple high-stress activities in one day will exponentially increase the burnout.
        Remember to only include each non set-time activity once per timetable (it should not appear on multiple different days in the same timetable)

        To add in the non set-time activities, select the day you wish to add it on, then the time (ensuring it does not conflict) and then add it (remember to do this for both timetables). The non set-time activities do not have to all be on the same day.
        Remember to spread the non set-time activities out over the entire week as to prevent too much stress. It is very bad to cram 3-4 of non set-time activcities into one day as this can cause severe burnout. Consider this heavily when making your judgement

        Finally, create a burnout score for each of the timetables. 
        0-25 = No-Low Stress, 25-50 = Low-Medium Stress, 50-75 = Medium-High Stress, 75-90 = High-Extreme Stress, 90-100 = Unmanageable Stress. Make sure to thing deeply about the stress rating given and than it should be consistent if i resubmit the same data.
        To determine the 'burnout score' make a perceptive, thoughtful and educated decision.
        For example, 0-1 activities on most days : 0-25 burnout score, 1-2 activities on most days : 25-50 burnout score, etc etc. 

        5. For any days with no items whatsoever, add a 'Free Day' item from '00:01' to '23:59'

        REMEMBER TO RETURN THE DATA IN THIS FORMAT:  [[{day:[{item: [startTime,finishTime]}, ...], ... },burnout_score] , [{day:[{item: [startTime,finishTime]}, ...], ... },burnout_score]]

        DO NOT ADD ANY TEXT BEFORE OR AFTER THE TIMETABLE. JUST RETURN IT IN PLAIN TEXT IN ONE LINE. THIS IS BECAUSE IT WILL BE READ BY A MACHINE   

        Here is an example:
        [[{'Monday': [{'School': ['08:30', '15:30']}, {'Arabic Reading': ['16:00', '18:00']}, {'Maths': ['18:30', '19:00']}, {'English': ['19:15', '19:45']}], 'Tuesday': [{'School': ['08:30', '15:30']}, {'Swimming': ['16:00', '16:45']}, {'Free Day': ['17:30', '19:30']}], 'Wednesday': [{'School': ['08:30', '15:30']}, {'Free Day': ['17:15', '19:30']}], 'Thursday': [{'School': ['08:30', '15:30']}, {'Free Day': ['17:30', '19:30']}], 'Friday': [{'School': ['08:30', '14:00']}, {'Free Day': ['14:00', '19:30']}], 'Saturday': [{'Basketball': ['10:00', '11:00']}, {'Free Day': ['12:00', '19:30']}], 'Sunday': [{'Free Day': ['08:00', '19:30']}]}, 48], [{'Monday': [{'School': ['08:30', '15:30']}, {'Arabic Reading': ['16:00', '18:00']}, {'English': ['18:30', '19:00']}, {'Maths': ['19:15', '19:45']}], 'Tuesday': [{'School': ['08:30', '15:30']}, {'Swimming': ['16:00', '16:45']}, {'Free Day': ['17:00', '19:30']}], 'Wednesday': [{'School': ['08:30', '15:30']}, {'Free Day': ['17:30', '19:30']}], 'Thursday': [{'School': ['08:30', '15:30']}, {'Free Day': ['17:15', '19:30']}], 'Friday': [{'School': ['08:30', '14:00']}, {'Free Day': ['14:00', '19:30']}], 'Saturday': [{'Basketball': ['10:00', '11:00']}, {'Free Day': ['11:15', '19:30']}], 'Sunday': [{'Free Day': ['08:00', '19:30']}]}, 44]]
        """

        final_prompt = prompt_part1 + prompt_part2 + prompt_part3 + prompt_part4 + prompt_part5
        # p1: introduction, p2: school timetable, p3: set-time activities, p4: non-set-time activities, p5: stress rating, return 2 timetables with burnout score, return in JSON

        return final_prompt

def minutes_to_hours(minutes):
    hours = minutes // 60  
    minutes = minutes % 60 
    return f"{hours:02}:{minutes:02}"  

app = Flask(__name__)

API = OPENAI_INSTANCE(api_key)


@app.route("/", methods=['POST', 'GET'])
def index():
    
    return render_template("index.html")

########################### DEBUG / TESTING FUNCTIONS ########################
TESTING_ENABLED = (os.getenv("TESTING_ENABLED") == '1')
@app.route("/test_call")
def test_call():
    if TESTING_ENABLED:
        tc_result = API.test_call()
    else:
        tc_result = "Testing mode disabled."
    return "<p>Test Call Result : '{}'</p>".format(tc_result)

@app.route("/sample_timetable")
def sample_timetable():
    if TESTING_ENABLED:
        return render_template("sample_results_page.html")
    else:
        return "Testing mode disabled."

@app.route("/sample_submission")
def sample_data_test():                         # /sample_submission?dataset=1 (crammed)         /sample_submission?dataset=2 (light)
    crammed_data = False
    light_data = False
    dataset_used = "Regular"
    try:
        dataset_int = int(request.args.get("dataset"))
        if dataset_int == 1:
            crammed_data = True
            dataset_used = "Crammed"
        elif dataset_int == 2:
            light_data = True
            dataset_used = "Light"
    except Exception as e:
        pass
    if TESTING_ENABLED:
        if crammed_data:
            test_prompt = API.create_prompt(sample_data.crammed.school_timetable, sample_data.crammed.set_time_activities, sample_data.crammed.home_activities)
        elif light_data:
            test_prompt = API.create_prompt(sample_data.light.school_timetable, sample_data.light.set_time_activities, sample_data.light.home_activities)
        else:
            test_prompt = API.create_prompt(sample_data.school_timetable, sample_data.set_time_activities, sample_data.home_activities)
        test_prompt_result = API.openai_call(test_prompt)
    else:
        test_prompt_result = "Testing mode disabled."
    return "<h3>Sample Data Result (Dataset {}): </h3><br><br><p>'{}'</p>".format(dataset_used,test_prompt_result)
###############################################################################

def remove_dupes(data):
    data = ast.literal_eval(data)
    for item in data:
        timetable, number = item
        activities_map = {}
        for day, activities in timetable.items():
            for activity_entry in activities:
                for activity, time in activity_entry.items():
                    if activity.lower() != "school" and activity.lower() != "free day":
                        if activity not in activities_map:
                            activities_map[activity] = []
                        activities_map[activity].append((day, time))
        for activity, occurrences in activities_map.items():
            if len(occurrences) > 1:
                day_activity_counts = {day: len(timetable[day]) for day, _ in occurrences}
                sorted_days = sorted(occurrences, key=lambda x: day_activity_counts[x[0]])
                keep_day = sorted_days[0][0]
                for day, _ in occurrences[1:]:
                    timetable[day] = [
                        entry for entry in timetable[day] if activity not in entry
                    ]
    return data


@app.route("/submit", methods=['POST','GET'])
def data_submission_route():
    form_data = request.get_json()
    #print(str(form_data))

    if request.method == 'POST':
        try:
            
            
            school_timetable = [form_data['school_timetable']['monday_to_thursday']['start_time'],form_data['school_timetable']['monday_to_thursday']['finish_time'], form_data['school_timetable']['friday']['start_time'],form_data['school_timetable']['friday']['finish_time']]
            
            set_time_activities = {}
            home_activities = {}

            for eca in form_data['ecas']:

                #import random
                #RANDOM_DAY = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][random.randint(0,6)]

                set_time_activities[eca['name']] = [eca['start_time'],eca['finish_time'], eca['type'], eca['stressfulness'],eca['date']]    

            for activity in form_data['other_activities']:
                home_activities[activity['name']] = [activity['type'],minutes_to_hours(int(activity['duration'])),activity['stressfulness']]


            concat = "{}\n\n{}\n\n{}".format(school_timetable,set_time_activities,home_activities)
            #print(concat)
            DB.append_timetable([school_timetable,set_time_activities,home_activities])
            API.db_routine(DB.no_of_timetables())

            return str(DB.no_of_timetables())
            #timetable_result = API.openai_call(API.create_prompt(school_timetable,set_time_activities,home_activities))
            #return "Timetable (Unformatted): {}".format(str(timetable_data))
        except Exception as e:
            print(e)
            return "Invalid Form Submission : Error Code 1"
    else:
        return "Invalid Form Submission : Error Code 2"


@app.route('/form')
def user_timetable_form():
    return render_template('form_4.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/timetable/<path:timetable>')
def serve_timetable(timetable):
    if os.path.isfile(JSON_DIRECTORY + "/{}_0.json".format(timetable)) and os.path.isfile(JSON_DIRECTORY + "/{}_1.json".format(timetable)):
        return render_template('results_page.html', timetable1="table_json/{}_{}.json".format(timetable,0), timetable2="table_json/{}_{}.json".format(timetable,1))
    try:
        raw_json = DB.return_result(timetable)
        print(raw_json)
        ######### POST-PROCESSING, ENSURE DATA IS VALID ############
        #raw_json = API.timetable_check(raw_json)
        raw_json = str(remove_dupes(raw_json))
        #print(raw_json)
        #raw_json = API.fix_json(raw_json)
        ############################################################
        
        json_timetable = json.loads(raw_json.replace("'",'"'))

        with open(JSON_DIRECTORY+"/{}_{}.json".format(timetable,0),"w") as timetable_1w:
            timetable_1w.write(str(json_timetable[0]).replace("'",'"'))
            timetable_1w.close()

        with open(JSON_DIRECTORY+"/{}_{}.json".format(timetable,1),"w") as timetable_2w:
            timetable_2w.write(str(json_timetable[1]).replace("'",'"'))
            timetable_2w.close()   

        return render_template('results_page.html', timetable1="table_json/{}_{}.json".format(timetable,0), timetable2="table_json/{}_{}.json".format(timetable,1))
    except Exception as e:
        print(e)
        return "Invalid DB Key"

@app.route("/table_json/<path:jsonfilename>")
def return_table_json(jsonfilename):
    return send_from_directory(JSON_DIRECTORY,jsonfilename)

@app.route('/csv_convert')
def download_schedule():
    json_filename = request.args.get('json')
    if not json_filename:
        return abort(400, description="Error Code 1 : JSON filename not provided")

    json_filepath = os.path.join(JSON_DIRECTORY, f"{json_filename}.json")

    if not os.path.isfile(json_filepath):
        return abort(404, description="JSON file not found.")

    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            schedule_data = json.load(f)[0]
    except Exception as e:
        return abort(500, description=f"Error reading JSON file: {e}")

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Day", "Activity", "Start Time", "End Time"])
    
    # Populate CSV with schedule data
    for day, activities in schedule_data.items():
        for activity in activities:
            for name, times in activity.items():
                writer.writerow([day, name, times[0], times[1]])
 
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=plAnnIt_timetable.csv"}
    )

if __name__ == "__main__":
    server = Server(app.wsgi_app)
    server.watch('templates/')
    server.serve(host='0.0.0.0', port=5000, debug=True)