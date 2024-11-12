# Setup

In order to playback MusicAgent generated Sonic PI files you'll need to load `Sonicpi/Setup/recording.rb` in your Sonic PI.
Make sure incoming OSC is enabled in your Sonic PI IDE to capture incoming messages.

**recording.rb**
```bash
live_loop :listen do
  use_real_time
  script = sync "/osc*/run-code"
  
  begin
    eval script[0]
    osc_send '127.0.0.1', 4559, '/feedback', 'MusicAgent Code was executed successfully'
  rescue Exception => e
    osc_send '127.0.0.1', 4559, '/feedback', e.message
  end
end
```