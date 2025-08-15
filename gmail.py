import streamlit as st
from arcadepy import Arcade
import base64
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API keys from .env
load_dotenv()
ARCADE_API_KEY = os.getenv("ARCADE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Page config
st.set_page_config(page_title="Automatic Email Sender", page_icon="📧")

st.title("📧 Automatic Email Sender with Gemini & Gmail API")
st.write("Generate and send emails automatically using Gemini + Gmail API.")

# Email details input
sender_email = st.text_input("Sender Gmail address (USER_ID)", placeholder="youremail@gmail.com")
recipient_email = st.text_input("Recipient Email Address", placeholder="friend@example.com")

# Input prompt from user
prompt_input = st.text_area(
    "Enter your email generation prompt:",
    placeholder="Write a warm and cheerful email inviting my friend Alex to my birthday party..."
)

# Subject input
subject_input = st.text_input("Email Subject", value="Birthday Party Invitation")

# Send button
if st.button("Generate & Send Email"):
    if not ARCADE_API_KEY or not GEMINI_API_KEY:
        st.error("Missing API keys. Please check your .env file.")
    elif not sender_email.strip() or not recipient_email.strip():
        st.warning("Please enter both sender and recipient email addresses.")
    elif not prompt_input.strip():
        st.warning("Please enter a prompt.")
    else:
        try:
            # 1. Authenticate with Gmail send scope via Arcade
            client = Arcade(api_key=ARCADE_API_KEY)
            auth_response = client.auth.start(
                sender_email,
                "google",
                scopes=["https://www.googleapis.com/auth/gmail.send"]
            )

            if auth_response.status != "completed":
                st.info(f"[Click here to authorize Google access]({auth_response.url})")
                auth_response = client.auth.wait_for_completion(auth_response)

            access_token = auth_response.context.token

            # 2. Generate email text with Gemini
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            gemini_response = model.generate_content(prompt_input)
            email_body = gemini_response.text.strip()

            # 3. Create MIME message
            raw_email = f"To: {recipient_email}\r\nSubject: {subject_input}\r\n\r\n{email_body}"
            encoded_email = base64.urlsafe_b64encode(raw_email.encode("utf-8")).decode("utf-8")

            # 4. Send email via Gmail API
            send_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {"raw": encoded_email}

            res = requests.post(send_url, headers=headers, json=payload)

            if res.status_code in (200, 201):
                st.success("✅ Email sent successfully!")
                st.text_area("Generated Email", email_body, height=200)
            else:
                st.error(f"❌ Failed to send email: {res.status_code} {res.text}")

        except Exception as e:
            st.error(f"Error: {e}")
