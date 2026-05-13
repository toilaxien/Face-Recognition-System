import re

filepath = r'd:\Project_by_myself\Face_Recognition_System\attendance_system\ui\index.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the old script tag line
content = content.replace('    <script src="/ui/script.js?v=2"></script>\n\n', '')

# Insert script tag right before </body>
content = content.replace('</body>', '    <script src="/ui/script.js?v=3"></script>\n</body>')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done - script tag moved after profileModal")
