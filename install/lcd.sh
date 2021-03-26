
# Start LCD
echo "Stating Jukebox LCD"
su - pi -c "cd /opt/jukebox; pipenv run start > /opt/jukebox/jukebox.log &"
