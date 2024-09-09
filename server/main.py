from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import subprocess

app = Flask(__name__)
CORS(app)

@app.route('/get_chapters', methods=['POST'])
def get_chapters():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'No video URL provided'}), 400

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(video_url, download=False)

            # Check for chapters
            if 'chapters' in video_info:
                chapters = video_info['chapters']
                video_title = video_info['title']
                thumbnail = video_info.get('thumbnail', '')

                chapter_data = []
                for chapter in chapters:
                    chapter_data.append({
                        'title': chapter['title'],
                        'start_time': chapter['start_time'],
                        'end_time': chapter['end_time'],
                        'thumbnail': thumbnail,
                        'video_title': video_title,
                    })

                return jsonify({'chapters': chapter_data})

            else:
                return jsonify({'error': 'No chapters found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download_chapter', methods=['POST'])
def download_chapter():
    data = request.json
    video_url = data.get('url')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    chapter_title = data.get('chapter_title')

    if not all([video_url, start_time, end_time, chapter_title]):
        return jsonify({'error': 'Missing parameters'}), 400

    output_filename = f"{chapter_title}.mp4"

    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio',
            'outtmpl': output_filename,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Split the video based on the chapter timestamps
        split_command = [
            'ffmpeg', '-i', output_filename,
            '-ss', str(start_time), '-to', str(end_time),
            '-c', 'copy', f'chapter_{output_filename}'
        ]
        subprocess.run(split_command, check=True)

        return send_file(f'chapter_{output_filename}', as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
