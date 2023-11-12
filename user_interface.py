import wx
import time
import wx.grid as gridlib
import pandas as pd
import threading
from job_seeker import JobSeeker

class JobSeekerFrame(wx.Frame):
    def __init__(self, parent, title):
        super(JobSeekerFrame, self).__init__(parent, title=title, size=(800, 600))

        self.panel = wx.Panel(self)
        self.job_seeker = None
        self.initUI()
        self.Centre()
        self.Show()

    def initUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Keywords
        self.keywords_label = wx.StaticText(self.panel, label="Keywords (comma-separated):")
        self.keywords_textctrl = wx.TextCtrl(self.panel)
        vbox.Add(self.keywords_label, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        vbox.Add(self.keywords_textctrl, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # Locations
        self.locations_label = wx.StaticText(self.panel, label="Locations (comma-separated):")
        self.locations_textctrl = wx.TextCtrl(self.panel)
        vbox.Add(self.locations_label, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        vbox.Add(self.locations_textctrl, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # Max Limit
        self.max_limit_label = wx.StaticText(self.panel, label="Maximum Number of Results:")
        self.max_limit_textctrl = wx.TextCtrl(self.panel)
        vbox.Add(self.max_limit_label, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        vbox.Add(self.max_limit_textctrl, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # Start Button
        self.start_button = wx.Button(self.panel, label="Start Scraping")
        self.start_button.Bind(wx.EVT_BUTTON, self.onScrape)
        vbox.Add(self.start_button, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        # Save Button
        self.save_button = wx.Button(self.panel, label="Save to CSV")
        self.save_button.Bind(wx.EVT_BUTTON, self.onSave)
        vbox.Add(self.save_button, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, 10)

        self.panel.SetSizer(vbox)

    def onScrape(self, event):
        keywords = [keyword.strip() for keyword in self.keywords_textctrl.GetValue().split(",")]
        locations = [location.strip() for location in self.locations_textctrl.GetValue().split(",")]
        max_limit = int(self.max_limit_textctrl.GetValue())

        if not keywords or not locations or max_limit <= 0:
            wx.MessageBox('Please check your inputs.', 'Input Error', wx.OK | wx.ICON_ERROR)
            return

        self.job_seeker = JobSeeker(keywords, locations, max_limit)

        # Run the scraping in a separate thread to prevent UI freezing
        threading.Thread(target=self.job_seeker.start).start()
        wx.MessageBox('Scraping started. Check console for progress.', 'Info', wx.OK | wx.ICON_INFORMATION)

        while not self.job_seeker.is_job_done():
            time.sleep(0.5)

        wx.MessageBox('Scraping complete. Please download the csv file.', 'Info', wx.OK | wx.ICON_INFORMATION)

    def onSave(self, event):
        if self.job_seeker and not self.job_seeker.get_results().empty:
            with wx.FileDialog(self, "Save CSV file", wildcard="CSV files (*.csv)|*.csv",
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind
                pathname = fileDialog.GetPath()
                try:
                    self.job_seeker.get_results().to_csv(pathname, index=False)
                    wx.MessageBox(f'Data saved to {pathname}', 'Success', wx.OK | wx.ICON_INFORMATION)
                except IOError:
                    wx.LogError(f'Cannot save current data to file {pathname}')
        
class JobSeekerApp(wx.App):
    def OnInit(self):
        frame = JobSeekerFrame(None, title="LinkedIn Job Scraper")
        frame.Show()
        return True

def main():
    app = JobSeekerApp()
    app.MainLoop()

if __name__ == '__main__':
    main()
