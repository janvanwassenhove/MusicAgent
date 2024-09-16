use_bpm 50

define :dark_imperial_march do
  use_synth :blade
  with_fx :reverb, room: 0.8 do
    play :e2, release: 0.5
    sleep 0.5
    play :e2, release: 0.5
    sleep 0.5
    play :e2, release: 0.5
    sleep 0.5
    play :c2, release: 0.375
    sleep 0.375
    play :g2, release: 0.125
    sleep 0.125
    play :e2, release: 0.5
    sleep 0.5
    play :c2, release: 0.375
    sleep 0.375
    play :g2, release: 0.125
    sleep 0.125
    play :e2, release: 1
    sleep 1
  end
end

define :dark_imperial_march_part_2 do
  use_synth :blade
  with_fx :distortion, distort: 0.7 do
    play :b2, release: 0.5
    sleep 0.5
    play :b2, release: 0.5
    sleep 0.5
    play :b2, release: 0.5
    sleep 0.5
    play :c3, release: 0.375
    sleep 0.375
    play :g2, release: 0.125
    sleep 0.125
    play :e2, release: 0.5
    sleep 0.5
    play :c2, release: 0.375
    sleep 0.375
    play :g2, release: 0.125
    sleep 0.125
    play :e2, release: 1
    sleep 1
  end
end

define :dark_imperial_march_part_3 do
  use_synth :blade
  with_fx :echo, phase: 0.25, decay: 2 do
    play :e3, release: 0.5
    sleep 0.5
    play :e2, release: 0.375
    sleep 0.375
    play :e2, release: 0.125
    sleep 0.125
    play :e3, release: 0.5
    sleep 0.5
    play :d3, release: 0.375
    sleep 0.375
    play :d3, release: 0.125
    sleep 0.125
    play :d3, release: 0.125
    sleep 0.125
    play :c3, release: 0.125
    sleep 0.125
    play :b2, release: 0.125
    sleep 0.125
    play :g2, release: 0.375
    sleep 0.375
    play :e2, release: 0.125
    sleep 0.125
    play :c2, release: 0.125
    sleep 0.125
    play :e2, release: 1
    sleep 1
  end
end

define :dark_imperial_march_part_4 do
  use_synth :blade
  with_fx :flanger, phase: 2, depth: 5 do
    play :b2, release: 0.5
    sleep 0.5
    play :g2, release: 0.5
    sleep 0.5
    play :g2, release: 0.5
    sleep 0.5
    play :g2, release: 0.125
    sleep 0.125
    play :g2, release: 0.125
    sleep 0.125
    play :g2, release: 0.125
    sleep 0.125
    play :g2, release: 0.125
    sleep 0.125
    play :f2, release: 0.125
    sleep 0.125
    play :f2, release: 0.125
    sleep 0.125
    play :f2, release: 0.125
    sleep 0.125
    play :e2, release: 0.125
    sleep 0.125
    play :e2, release: 0.125
    sleep 0.125
    play :e2, release: 0.125
    sleep 0.125
    play :d2, release: 0.125
    sleep 0.125
    play :d2, release: 0.125
    sleep 0.125
    play :d2, release: 0.125
    sleep 0.125
    play :c2, release: 0.125
    sleep 0.125
    play :g2, release: 0.125
    sleep 0.125
    play :c2, release: 1
    sleep 1
  end
end

dark_imperial_march
dark_imperial_march_part_2
dark_imperial_march_part_3
dark_imperial_march_part_4