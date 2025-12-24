In order to run the streamlit script of GenAI on AWS, for example for the use case of the MCQ generation, follow the steps below

Step 1: First login to the AWS: https://aws.amazon.com/console/
Step 2: Search about the EC2 Instance
Step 3: Configure the UBUNTU Machine
Step 4: Launch the Instance
Step 5: Update the Machine

Setting up EC2-UBUNTU-AWS instance
Login-> Go to EC2->Instances->Select the Instance and Connect
1. sudo apt update
2. sudo apt-get update
3. sudo apt upgrade -y
4. sudo apt install git curl unzip tar make sudo vim wget -y
5. git clone https://github.com/mahfida/mcqgen.git
6. cd mcqgen

### If you want to add openai api key
7. touch .env
8. vim .env (and paste your api key there, assign to a variable)


9. sudo apt install python3-pip
10. sudo apt update
sudo apt install -y python3-venv python3-full
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

11. python3 -m streamlit run StreamlitAPP.py
- Go to your instance, copy the public IP and paste in your browser. (34.205.26.45:8501)
- But first configure the port number
	- Go to the Instance and Security->Security groups-> Edit Inbound Rules->Add Rule (Keep it Custom tcp) -> Port Range (8501)-> Source (0.0.0.0/0)
