# Daft Punk - Aerodynamic

use_bpm 123

maquillage = "il-macquillage-lady.wav"
aerodynamic = "funk.wav"

load_sample maquillage
load_sample aerodynamic

define :sample_chunk do |what, beat, dur, delay|
  beat = beat / 16.0
  dur = dur / 16.0
  sample what, beat_stretch: 16, start: beat, finish: beat + dur
  sleep delay
end

define :funk do
  # sample_chunk(aerodynamic, 0.0, 4.0, 4.0)
  
  sample_chunk(maquillage, 0.0, 0.5, 0.5)
  sample_chunk(maquillage, 2.5, 1.0, 0.25)
  sample_chunk(maquillage, 3.5, 0.5, 0.75)
  sample_chunk(maquillage, 0.0, 0.5, 0.5)
  sample_chunk(maquillage, 8.5, 0.5, 0.5)
  sample_chunk(maquillage, 2.5, 1.0, 1.0)
  sample_chunk(maquillage, 7.5, 0.5, 0.5)
  
  # sample_chunk(aerodynamic, 4.0, 4.0, 4.0)
  
  sample_chunk(maquillage, 3.5, 0.5, 0.5)
  sample_chunk(maquillage, 2.5, 1.0, 1.0)
  sample_chunk(maquillage, 7.5, 0.5, 0.5)
  sample_chunk(maquillage, 8.5, 0.5, 0.5)
  sample_chunk(maquillage, 2.5, 1.0, 1.0)
  sample_chunk(maquillage, 7.5, 0.5, 0.5)
  
  # sample_chunk(aerodynamic, 8.0, 4.0, 4.0)
  
  sample_chunk(maquillage, 0.0, 0.5, 0.5)
  sample_chunk(maquillage, 2.5, 1.0, 0.25)
  sample_chunk(maquillage, 3.5, 0.5, 0.75)
  sample_chunk(maquillage, 0.0, 0.5, 0.5)
  sample_chunk(maquillage, 8.5, 0.5, 0.5)
  sample_chunk(maquillage, 2.5, 1.0, 1.0)
  sample_chunk(maquillage, 7.5, 0.5, 0.5)
  
  # sample_chunk(aerodynamic, 12.0, 4.0, 4.0)
  
  sample_chunk(maquillage, 3.5, 0.5, 0.5)
  sample_chunk(maquillage, 8.5, 0.25, 0.0)
  sample_chunk(maquillage, 2.5, 1.0, 0.25)
  sample_chunk(maquillage, 3.5, 0.5, 0.5)
  sample_chunk(maquillage, 8.5, 0.25, 0.25)
  sample_chunk(maquillage, 3.5, 0.5, 0.5)
  sample_chunk(maquillage, 8.5, 0.5, 0.5)
  sample_chunk(maquillage, 2.5, 1.0, 1.0)
  sample_chunk(maquillage, 7.5, 0.5, 0.5)
end

# Live loops

live_loop :main do
  sleep 4
end

live_loop :funk do
  sync :main
  
  with_fx :ixi_techno, mix: 0.1, phase: 8, cutoff_min: 90, cutoff_max: 120, res: 0.9, amp: 1 do
    with_fx :bpf, mix: 0, res: 0.00001, centre: :B8, amp: 2 do
      funk
    end
  end
end

live_loop :solo do
  sync :main
  
  use_synth :zawa
  use_synth_defaults attack: 0.05, sustain: 0.15, release: 0.125
  
  phases = [
    [:D4, :Fs3, :B3, :Fs3],
    [:D4, :Gs3, :B3, :Gs3],
    [:G4, :B3, :E4, :B3],
    [:E4, :A3, :Cs4, :A3],
    
    [:D4, :Fs4, :B3, :Fs4],
    [:D4, :Gs4, :B3, :Gs4],
    [:G4, :B3, :E4, :B3],
    [:E4, :A3, :Cs4, :A3],
  ]
  
  phases.each do |notes|
    4.times do
      notes.each do |n|
        play n
        sleep 0.25
      end
    end
  end
end

live_loop :extra_beat do
  sync :main
  
  32.times do
    tick
    sample :bd_fat, amp: 2 if spread(1, 16).look
    sample :bd_fat, amp: 1.5 if spread(1, 32).rotate(4).look
    synth :cnoise, release: 0.6, cutoff: 130, env_curve: 7, amp: 1 if spread(1, 16).rotate(8).look
    synth :cnoise, release: 0.1, cutoff: 130, env_curve: 7, amp: 0.25 if spread(1, 2).look
    sleep 0.125
  end
end

live_loop :intro do
  stop # remove me if you want bells
  
  sync :main
  
  use_synth :pretty_bell
  use_synth_defaults release: 9
  
  with_fx :level, amp: 0.5 do
    4.times do
      with_fx :gverb, room: 20 do
        play :A1, amp: 0.25
        play :A2, amp: 0.5
        play :A3, amp: 1.5
        play :A4, amp: 0.75
        play :A5, amp: 0.5
        sleep 8
      end
    end
  end
end