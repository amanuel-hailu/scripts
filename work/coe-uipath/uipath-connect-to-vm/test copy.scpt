property logFile : "/Users/aman-mac-work/Desktop/RDP_Script_Log.txt" -- Set path just once

on logToFile(message)
	do shell script "echo " & quoted form of message & " >> " & quoted form of logFile
end logToFile

on listToString(aList)
	set oldDelimiters to AppleScript's text item delimiters
	set AppleScript's text item delimiters to ", "
	set aString to aList as string
	set AppleScript's text item delimiters to oldDelimiters
	return aString
end listToString

-- Clear the log file
do shell script "echo '' > " & quoted form of logFile -- use quoted form for file path
logToFile("Log file cleared.")

set filePath to POSIX file "/Users/aman-mac-work/Downloads/CampTek.rdp"
logToFile("1. File path set to: " & POSIX path of filePath)

tell application "Finder"
	activate
	open filePath
end tell
logToFile("2. Finder activated and file opened")

delay 5 -- Wait for the Microsoft Remote Desktop to open and load
logToFile("3. Delayed for 5 seconds to allow Microsoft Remote Desktop to open and load")

tell application "System Events"
	tell process "Microsoft Remote Desktop"
		set frontmost to true
		my logToFile("4. Microsoft Remote Desktop process set to frontmost")
		
		delay 5 -- Adjust this delay as needed
		
		try
			-- Log details of the front window
			set windowElements to entire contents of front window
			set numElements to count windowElements
			my logToFile("5. Number of elements in the window: " & numElements)
			
			-- Try to interact with the text field
			set value of text field 2 of front window to "PASSWORD123"
			my logToFile("6. Password entered in the password field.")
			
			-- Click the "Continue" button
			click button "Continue" of front window
			my logToFile("7. Clicked the 'Continue' button.")
			
		on error errMsg
			my logToFile("Error interacting with the dialog: " & errMsg)
		end try
	end tell
end tell

