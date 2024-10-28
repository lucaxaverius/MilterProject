import Milter
import email
import sys
import requests
from io import BytesIO
import time
from Milter.utils import parse_addr
from socket import AF_INET, AF_INET6
from multiprocessing import Process as Thread, Queue
from email.message import EmailMessage

logq = Queue(maxsize=4)

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
                else:
                    self.log(f"Failed to send attachment {filename}: {response.status_code}")
    
        return Milter.ACCEPT
        
    def log(self, message):
        """
        Logs messages to the shared logging queue.

        Args:
            message (str): The message to be logged.
        """
        logq.put((message, self.id, time.time()))

def background_log():
    """
    Background thread to process and print log messages from the logging queue.
    """
    while True:
        log_entry = logq.get()
        if log_entry is None:
            break
        msg, id, timestamp = log_entry
        print(f"{time.strftime('%Y-%b-%d %H:%M:%S', time.localtime(timestamp))} [{id}] {msg}")

def main():
    """
    Main function to start the Milter and logging process.
    Sets up the Milter to listen on a specified socket and handles incoming email messages.
    """
    log_thread = Thread(target=background_log)
    log_thread.start()
    
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

    logq.put(None)
    log_thread.join()
    print(f"{time.strftime('%Y-%b-%d %H:%M:%S')} - SimpleMilter arrestato.")

if __name__ == "__main__":
    main()
