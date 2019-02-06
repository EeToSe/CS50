from cs50 import get_string
import sys

"""Load dictionary into memory, returning true if successful else false"""
if len(sys.argv) != 2:
    sys.exit("Usage: python bleep.py")

file = open(sys.argv[1], "r")
bannedWords = set()
for line in file:
    bannedWords.add(line.rstrip("\n"))
file.close()
message = get_string("What message would you like to censor?\n")
messageList = message.split(' ')
newmessage = ''
for word in messageList:
    if word.lower() in bannedWords:
        word = '*'*len(word)
    newmessage += word + ' '
print(newmessage)

