# White Stripes - 7 nations Army

use_bpm 124

in_thread do
  with_fx :distortion, distort: 0.6, amp: 0.5 do
    use_synth :bass_foundation
    live_loop :gtr do
      3.times do
        play :A2
        sleep 1.5
        play :A2
        sleep 0.5
        play :C3
        sleep 0.75
        play :A2
        sleep 0.75
        play :G2
        sleep 0.5
        play :F2
        sleep 2
        play :E2
        sleep 2
      end
      play :A2
      sleep 1.5
      play :A2
      sleep 0.5
      play :C3
      sleep 0.75
      play :A2
      sleep 0.75
      play :G2
      sleep 0.5
      play :F2
      sleep 0.75
      play :G2
      sleep 0.75
      play :F2
      sleep 0.5
      play :E2
      sleep 2
    end
  end
end

in_thread do
  live_loop :drum do
    sample :drum_bass_hard
    sleep 1
  end

  live_loop :cym do
    sleep 1
    sample :drum_snare_hard, amp: 0.5
    sleep 1
  end
end