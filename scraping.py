import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter.scrolledtext as scrolledtext
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
import threading
import queue
import os
from datetime import datetime
import json

class WebScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Web Scraper")
        self.root.geometry("1000x800")
        
        # Configure theme
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # URL Input Section
        self.url_frame = ctk.CTkFrame(self.main_frame)
        self.url_frame.pack(fill="x", padx=5, pady=5)
        
        self.url_label = ctk.CTkLabel(self.url_frame, text="Enter URL:")
        self.url_label.pack(side="left", padx=5, pady=5)
        
        self.url_entry = ctk.CTkEntry(self.url_frame, width=500)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        # Options Frame
        self.options_frame = ctk.CTkFrame(self.main_frame)
        self.options_frame.pack(fill="x", padx=5, pady=5)
        
        # Depth Options
        self.depth_label = ctk.CTkLabel(self.options_frame, text="Depth:")
        self.depth_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.depth_var = ctk.StringVar(value="1")
        self.depth_entry = ctk.CTkEntry(self.options_frame, width=50, textvariable=self.depth_var)
        self.depth_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Delay Options
        self.delay_label = ctk.CTkLabel(self.options_frame, text="Delay (s):")
        self.delay_label.grid(row=0, column=2, padx=5, pady=5)
        
        self.delay_var = ctk.StringVar(value="1")
        self.delay_entry = ctk.CTkEntry(self.options_frame, width=50, textvariable=self.delay_var)
        self.delay_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Max Pages Options
        self.max_pages_label = ctk.CTkLabel(self.options_frame, text="Max Pages:")
        self.max_pages_label.grid(row=0, column=4, padx=5, pady=5)
        
        self.max_pages_var = ctk.StringVar(value="50")
        self.max_pages_entry = ctk.CTkEntry(self.options_frame, width=50, textvariable=self.max_pages_var)
        self.max_pages_entry.grid(row=0, column=5, padx=5, pady=5)
        
        # Scraping Type
        self.scraping_type_label = ctk.CTkLabel(self.options_frame, text="Scraping Type:")
        self.scraping_type_label.grid(row=1, column=0, padx=5, pady=5)
        
        self.scraping_type_var = ctk.StringVar(value="links")
        self.scraping_type_menu = ctk.CTkOptionMenu(
            self.options_frame, 
            values=["links", "text", "images", "all"],
            variable=self.scraping_type_var
        )
        self.scraping_type_menu.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        
        # Output Format
        self.output_format_label = ctk.CTkLabel(self.options_frame, text="Output Format:")
        self.output_format_label.grid(row=1, column=3, padx=5, pady=5)
        
        self.output_format_var = ctk.StringVar(value="text")
        self.output_format_menu = ctk.CTkOptionMenu(
            self.options_frame, 
            values=["text", "json", "csv"],
            variable=self.output_format_var
        )
        self.output_format_menu.grid(row=1, column=4, columnspan=2, padx=5, pady=5)
        
        # Button Frame
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_button = ctk.CTkButton(
            self.button_frame, 
            text="Start Scraping", 
            command=self.start_scraping_thread
        )
        self.start_button.pack(side="left", padx=5, pady=5)
        
        self.stop_button = ctk.CTkButton(
            self.button_frame, 
            text="Stop", 
            command=self.stop_scraping,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=5, pady=5)
        
        self.save_button = ctk.CTkButton(
            self.button_frame, 
            text="Save Results", 
            command=self.save_results,
            state="disabled"
        )
        self.save_button.pack(side="right", padx=5, pady=5)
        
        # Progress Frame
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", padx=5, pady=5)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Progress:")
        self.progress_label.pack(side="left", padx=5, pady=5)
        
        self.progress_var = ctk.StringVar(value="Ready")
        self.progress_status = ctk.CTkLabel(self.progress_frame, textvariable=self.progress_var)
        self.progress_status.pack(side="left", padx=5, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", expand=True, padx=5, pady=5)
        self.progress_bar.set(0)
        
        # Results Frame
        self.results_frame = ctk.CTkFrame(self.main_frame)
        self.results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.results_text = scrolledtext.ScrolledText(
            self.results_frame,
            wrap="word",
            font=("Consolas", 10)
        )
        self.results_text.pack(fill="both", expand=True)
        
        # Initialize scraper variables
        self.scraping_active = False
        self.scraped_data = []
        self.visited_urls = set()
        self.queue = queue.Queue()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]
        
    def start_scraping_thread(self):
        """Start scraping in a separate thread to keep the GUI responsive."""
        if not self.url_entry.get():
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        # Reset variables
        self.scraped_data = []
        self.visited_urls = set()
        self.results_text.delete(1.0, "end")
        self.progress_bar.set(0)
        
        # Get parameters
        try:
            depth = int(self.depth_var.get())
            delay = float(self.delay_var.get())
            max_pages = int(self.max_pages_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for depth, delay, and max pages")
            return
            
        # Update UI
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.save_button.configure(state="disabled")
        self.progress_var.set("Starting...")
        self.scraping_active = True
        
        # Start thread
        threading.Thread(
            target=self.scrape_website,
            args=(self.url_entry.get(), depth, delay, max_pages),
            daemon=True
        ).start()
        
    def scrape_website(self, start_url, depth, delay, max_pages):
        """Main scraping function that handles crawling and scraping."""
        try:
            base_domain = urlparse(start_url).netloc
            self.queue.put((start_url, 0))
            processed_pages = 0
            
            while not self.queue.empty() and self.scraping_active and processed_pages < max_pages:
                current_url, current_depth = self.queue.get()
                
                if current_url in self.visited_urls or current_depth > depth:
                    continue
                    
                if urlparse(current_url).netloc != base_domain:
                    continue
                    
                try:
                    # Random delay to avoid being blocked
                    time.sleep(delay * random.uniform(0.5, 1.5))
                    
                    # Get page with random user agent
                    headers = {"User-Agent": random.choice(self.user_agents)}
                    response = requests.get(
                        current_url,
                        headers=headers,
                        timeout=10,
                        allow_redirects=True
                    )
                    
                    if response.status_code != 200:
                        self.update_progress(f"Failed to fetch {current_url} - Status: {response.status_code}")
                        continue
                        
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Process the page based on scraping type
                    scraped_content = self.process_page(current_url, soup)
                    self.scraped_data.append(scraped_content)
                    
                    # Update progress
                    processed_pages += 1
                    progress = min(processed_pages / max_pages, 1.0)
                    self.update_progress(f"Scraped {current_url} (Depth: {current_depth})", progress)
                    
                    # Find links for further crawling
                    if current_depth < depth:
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            absolute_url = urljoin(current_url, href)
                            
                            # Only follow links from the same domain
                            if urlparse(absolute_url).netloc == base_domain:
                                if absolute_url not in self.visited_urls:
                                    self.queue.put((absolute_url, current_depth + 1))
                    
                    self.visited_urls.add(current_url)
                    
                except Exception as e:
                    self.update_progress(f"Error processing {current_url}: {str(e)}")
                    continue
                    
            # Scraping completed
            self.scraping_active = False
            self.update_progress(f"Scraping completed. Processed {processed_pages} pages.", 1.0)
            self.display_results()
            
        except Exception as e:
            self.update_progress(f"Fatal error: {str(e)}", 0)
            
        finally:
            self.root.after(0, self.on_scraping_complete)
            
    def process_page(self, url, soup):
        """Process a single page based on the selected scraping type."""
        scraped_content = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "links": [],
            "text": "",
            "images": []
        }
        
        scraping_type = self.scraping_type_var.get()
        
        if scraping_type in ["links", "all"]:
            scraped_content["links"] = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
            
        if scraping_type in ["text", "all"]:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            scraped_content["text"] = text
            
        if scraping_type in ["images", "all"]:
            scraped_content["images"] = [urljoin(url, img['src']) for img in soup.find_all('img', src=True)]
            
        return scraped_content
        
    def display_results(self):
        """Display the scraped results in the text widget."""
        output_format = self.output_format_var.get()
        
        if output_format == "text":
            for item in self.scraped_data:
                self.results_text.insert("end", f"URL: {item['url']}\n")
                self.results_text.insert("end", f"Timestamp: {item['timestamp']}\n")
                
                if item['links']:
                    self.results_text.insert("end", "Links:\n")
                    for link in item['links']:
                        self.results_text.insert("end", f"- {link}\n")
                        
                if item['text']:
                    self.results_text.insert("end", "Text Content:\n")
                    self.results_text.insert("end", f"{item['text'][:500]}...\n\n")  # Show first 500 chars
                    
                if item['images']:
                    self.results_text.insert("end", "Images:\n")
                    for img in item['images']:
                        self.results_text.insert("end", f"- {img}\n")
                        
                self.results_text.insert("end", "\n" + "="*80 + "\n\n")
                
        elif output_format == "json":
            self.results_text.insert("end", json.dumps(self.scraped_data, indent=2))
            
        elif output_format == "csv":
            # Simple CSV representation
            self.results_text.insert("end", "URL,Timestamp,LinkCount,TextLength,ImageCount\n")
            for item in self.scraped_data:
                self.results_text.insert("end", 
                    f"{item['url']},{item['timestamp']},{len(item['links'])},{len(item['text'])},{len(item['images'])}\n")
                    
    def save_results(self):
        """Save the scraped results to a file."""
        if not self.scraped_data:
            messagebox.showwarning("Warning", "No data to save")
            return
            
        output_format = self.output_format_var.get()
        file_types = {
            "text": [("Text files", "*.txt")],
            "json": [("JSON files", "*.json")],
            "csv": [("CSV files", "*.csv")]
        }
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{output_format}",
            filetypes=file_types[output_format],
            title="Save Scraped Data"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if output_format == "text":
                    for item in self.scraped_data:
                        f.write(f"URL: {item['url']}\n")
                        f.write(f"Timestamp: {item['timestamp']}\n")
                        
                        if item['links']:
                            f.write("Links:\n")
                            for link in item['links']:
                                f.write(f"- {link}\n")
                                
                        if item['text']:
                            f.write("Text Content:\n")
                            f.write(f"{item['text']}\n\n")
                            
                        if item['images']:
                            f.write("Images:\n")
                            for img in item['images']:
                                f.write(f"- {img}\n")
                                
                        f.write("\n" + "="*80 + "\n\n")
                        
                elif output_format == "json":
                    json.dump(self.scraped_data, f, indent=2)
                    
                elif output_format == "csv":
                    f.write("URL,Timestamp,LinkCount,TextLength,ImageCount\n")
                    for item in self.scraped_data:
                        f.write(f"{item['url']},{item['timestamp']},{len(item['links'])},{len(item['text'])},{len(item['images'])}\n")
                        
            messagebox.showinfo("Success", f"Data saved successfully to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            
    def stop_scraping(self):
        """Stop the ongoing scraping process."""
        self.scraping_active = False
        self.update_progress("Scraping stopped by user", self.progress_bar.get())
        
    def update_progress(self, message, progress=None):
        """Update the progress status and progress bar."""
        self.root.after(0, lambda: self._update_progress_gui(message, progress))
        
    def _update_progress_gui(self, message, progress):
        """Helper function to update GUI elements from the main thread."""
        self.progress_var.set(message)
        if progress is not None:
            self.progress_bar.set(progress)
        self.results_text.insert("end", message + "\n")
        self.results_text.see("end")
        self.root.update_idletasks()
        
    def on_scraping_complete(self):
        """Clean up after scraping is complete."""
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.save_button.configure(state="normal")
        
if __name__ == "__main__":
    root = ctk.CTk()
    app = WebScraperApp(root)
    root.mainloop()