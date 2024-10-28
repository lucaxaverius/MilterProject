import Milter
import email
import sys
import requests
from io import BytesIO
import time
from Milter.utils import parse_addr
from socket import AF_INET, AF_INET6
from multiprocessing import Process as Thread
from email.message import EmailMessage

class SimpleMilter(Milter.Base):
    """
    A custom Milter to process email messages and simulate interaction with a REST API.
    This Milter connects to Postfix, processes email messages, and interacts with an API endpoint when attachments are detected.
    """

    def __init__(self):
        """
        Initializes a new instance of the SimpleMilter class.
        Each connection runs in its own thread and has its own SimpleMilter instance.
        """
        self.id = Milter.uniqueID()  # Unique ID for each connection
        self.fp = None  # Buffer to store email content

    @Milter.noreply
    def connect(self, IPname, family, hostaddr):
        """
        Called when a new SMTP connection is established.
        Logs the connection details.

        Args:
            IPname (str): Hostname of the connecting client.
            family: Address family (e.g., AF_INET).
            hostaddr (tuple): Tuple containing IP address and port.
        """
        self.IP = hostaddr[0]
        self.port = hostaddr[1]
        self.IPname = IPname
        self.H = None
        self.fp = None
        self.log(f"Connessione da {IPname} all'indirizzo {hostaddr}")
        return Milter.CONTINUE

    def envfrom(self, mailfrom, *str):
        """
        Called when the MAIL FROM command is received.
        Initializes the buffer to store the email content.

        Args:
            mailfrom (str): The sender's email address.
        """
        self.fp = BytesIO()  # Initialize buffer as BytesIO for binary handling
        self.fp.write(f"From {mailfrom} {time.ctime()}\n".encode('utf-8'))  # Write initial email info as bytes
        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name, hval):
        """
        Called for each email header.
        Writes the header to the buffer.

        Args:
            name (str): The header name.
            hval (str): The header value.
        """
        self.fp.write(f"{name}: {hval}\n".encode('utf-8'))
        return Milter.CONTINUE

    @Milter.noreply
    def eoh(self):
        """
        Called at the end of the headers.
        Adds a newline to separate headers from the body.
        """
        self.fp.write("\n".encode('utf-8'))
        return Milter.CONTINUE

    @Milter.noreply
    def body(self, chunk):
        """
        Called for each chunk of the email body.
        Writes the body chunk to the buffer.

        Args:
            chunk (bytes): A chunk of the email body.
        """
        self.fp.write(chunk)
        return Milter.CONTINUE

    def eom(self):
        """
        Called at the end of the message.
        Processes the email to find attachments and interacts with an example REST API.
        """
        self.fp.seek(0)
        msg = email.message_from_bytes(self.fp.read(), _class=EmailMessage)  # Parse email from bytes
        
        # Iterate over parts to find attachments
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                file_data = part.get_payload(decode=True)
                
                # Simulate API request to send the attachment
                files = {'file': (filename, file_data)}
                response = requests.post("https://jsonplaceholder.typicode.com/posts", files=files)
                
                if response.status_code == 201:
                    self.log(f"Attachment {filename} sent successfully.")
                    # Extract the 'body' field from the response (assuming JSON format)
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        response_body = response_data[0].get("body", "No body found in response")
                        self.log(f"Response Body: {response_body}")
                    else:
                        self.log(f"Unexpected response format: {response.text}")
                else:
                    self.log(f"Failed to send attachment {filename}: {response.status_code}")
                    self.log(f"Response: {response.text}")
    
        return Milter.ACCEPT
        
    def log(self, message):
        """
        Logs messages directly to a log file.

        Args:
            message (str): The message to be logged.
        """
        timestamp = time.strftime('%Y-%b-%d %H:%M:%S', time.localtime(time.time()))
        with open('/var/log/simple_milter.log', 'a') as log_file:
            log_file.write(f"{timestamp} [{self.id}] {message}\n")

def main():
    """
    Main function to start the Milter and logging process.
    Sets up the Milter to listen on a specified socket and handles incoming email messages.
    """
    # Define the socket to listen on (TCP socket on localhost:9900)
    socketname = "inet:9900@localhost"
    timeout = 600

    # Set up the Milter factory and flags
    Milter.factory = SimpleMilter
    flags = Milter.CHGBODY + Milter.ADDHDRS + Milter.ADDRCPT
    Milter.set_flags(flags)

    print(f"{time.strftime('%Y-%b-%d %H:%M:%S')} - SimpleMilter avviato, daje.")
    sys.stdout.flush()
    Milter.runmilter("simplefilter", socketname, timeout)

    print(f"{time.strftime('%Y-%b-%d %H:%M:%S')} - SimpleMilter arrestato.")

if __name__ == "__main__":
    main()
