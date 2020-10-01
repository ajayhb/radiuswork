Project name: radiusagent

App Name: buyerinfo

A) Setup:

    1) Download and install python3 on terminal. Confirm by python3 --version
    2) Clone this repository.
    3) Switch to codebranch
    4) cd into main project directory where you have files: manage.py, utils, buyerinfo etc.
    5) create a virtual environment by:

        sudo apt-get install python3-pip
        sudo pip3 install virtualenv
        virtualenv -p python3.x <venv_name> (venv_name is any name that you provide) (in place of python3.x, use the same version that you installed. eg. python3.8) 
        source <venv_name>/bin/activate

    6) After activating the virtual environment, download the requirements by running the command:
       pip install -r requirements.txt

    7) Fill in the utils/secrets.json values with your db credentials.
    8) Make sure that mysql server is on and working. And the table exists.
    9) on line 29 in buyerinfo/views.py file, change the path from where you're importing a CSV file with latitude and longitude dumps.
    10) run the commands:

        python manage.py migrate
        python manage.py runserver 0.0.0.0:8000
   

B) Assumptions and References:

    1) MySql table name is sellerdata. Can be changed to property on line 212 of buyerinfo/views.py if required.
    2) MySql query used for table:
    
        create TABLE sellerdata(
            id INT AUTO_INCREMENT PRIMARY KEY,
            isAvailable boolean not null default 0,
            latitude DOUBLE,
            longitude DOUBLE,
            price DOUBLE,
            bedrooms INT,
            bathrooms INT
         );
         
     3) CSV file for latitude and longitude dumps: https://support.spatialkey.com/spatialkey-sample-csv-data/
     4) Referral for (min and max latitude) and (min and max longitude) formulae: 
         https://www.movable-type.co.uk/scripts/latlong-db.html
         
     5) Scores of Distance and budget will take values among (30, 25, 20, 15, 10) and (30, 20, 15, 10) respectively.
     6) Scores of Bedroom and Bathroom each will take values among (20, 15, 10).


C) Apis to test out:
    1) populate_seller_table/ API that populates the MySql table with following values:
        1) latitude and longitude from csv 
       cURL request:
          curl --location --request POST 'http://127.0.0.1:8000/populate_seller_table/'
      
    
    2) search_result/ API that gives the UI, a list of values fetched from db which matches the search conditions.
    
      cURL request:
         curl --location --request POST 'http://127.0.0.1:8000/search_result/' \
        --header 'Content-Type: application/json' \
        --data-raw '{
        "latitude":30.10062,
        "longitude": -81.703751,
        "minBudget":200,
        "maxBudget": 1000,
        "minBathrooms":4,
        "maxBathrooms": 10,
        "minBedrooms":2,
        "maxBedrooms":8
        }'
        
        (remove the param that you don't want to pass among minBudget/ maxBudget, minBathrooms/maxBathrooms and minBedrooms/maxBedrooms).
