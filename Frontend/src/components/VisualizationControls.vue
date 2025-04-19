<template>
  <div>
    <div class="controls mb-2">
      <div class="time-scale-icons">
        <button
          :class="['time-scale-btn', { active: timeScale === 'seconds' }]"
          @click="setTimeScale('seconds')"
          title="Seconds"
        >
          <i class="fas fa-clock"></i>
        </button>
        <button
          :class="['time-scale-btn', { active: timeScale === 'milliseconds' }]"
          @click="setTimeScale('milliseconds')"
          title="Milliseconds"
        >
          <i class="fas fa-stopwatch"></i>
        </button>
        <button
          :class="['time-scale-btn', { active: timeScale === 'beats' }]"
          @click="setTimeScale('beats')"
          title="Beats (4 bars)"
        >
          <i class="fas fa-music"></i>
        </button>
      </div>
    </div>

    <div class="visualization-container">
      <div class="timeline-row">
        <div class="layer-name"></div>
        <div class="layer-track timeline-track">
          <div
            v-for="i in 20"
            :key="'tick-' + i"
            class="timeline-tick"
            :style="{ left: ((i - 1) * 5) + '%' }"
          >
            &nbsp;{{ formatTickLabel((i - 1) * (totalDuration / 20), 1) }}
          </div>
        </div>
      </div>
      <div
        v-for="(layer, index) in visualizationLayers"
        :key="'layer-' + index"
        class="visualization-row"
      >
        <div class="layer-name" @click="toggleLayer(index)">
          {{ layer[0]?.name }}
        </div>
        <div class="layer-track">
          <div
            v-for="(segment, segIndex) in layer"
            :key="segIndex"
            :class="['segment-wrapper']"
            :style="segment.style"
          >
            <div
              :class="['segment', segment.class, segment.fxClass, segment.infinite ? 'infinite-loop' : '']"
            >
              {{ segment.label }}
              <div class="custom-tooltip-wrapper">
                <div class="custom-tooltip" v-html="segment.tooltip"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VisualizationControls',
  props: {
    sonicPiCode: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      visualizationLayers: [],
      totalDuration: 60, 
      timeScale: 'seconds', // 'seconds', 'milliseconds', or 'beats'
      collapsedLayers: [],
    };
  },
  watch: {
    sonicPiCode: {
      immediate: true,
      handler(newCode) {
        this.generateVisualization(newCode);
      },
    },
  },
  methods: {
    parseSonicPiCode(code) {
      const keywordRegex = /\b(live_loop|play|sleep)\b/g;
      const numberRegex = /\b\d+(\.\d+)?\b/g;
      const functionRegex = /(:\w+)/g;
      const doendRegex = /\b(do|end)\b/g;

      code = code.replace(keywordRegex, '<span class="keyword">$&</span>');
      code = code.replace(numberRegex, '<span class="number">$&</span>');
      code = code.replace(functionRegex, '<span class="function">$&</span>');
      code = code.replace(doendRegex, '<span class="doend">$&</span>');

      return code;
    },
    formatTickLabel(value) {
        switch (this.timeScale) {
            case 'milliseconds': {
            return `${(value * 1000).toFixed(0)}ms`;
            }
            case 'beats': {
            const bpmMatch = this.sonicPiCode.match(/use_bpm\s+([\d.]+)/);
            const bpm = bpmMatch ? parseFloat(bpmMatch[1]) : 130; // default to 130 BPM if not specified
            return `${(value / 60 * bpm / 4).toFixed(1)} bars`;
            }
            default: {
            return `${value.toFixed(1)}s`;
            }
        }
    },
    setTimeScale(scale) {
      this.timeScale = scale;
    },
    toggleLayer(index) {
      this.$emit('toggle-layer', index);
    },
    generateVisualization() {
      const lines = this.sonicPiCode.split('\n');
      const layersMap = new Map();
      const threads = [];
      const loopStartTimes = {};
      this.defines = {};
      let totalDuration = 0;
      let currentThread = null;
      const threadStack = [];
      const fxStack = [];
      let globalTime = 0;
      let liveLoopBodies = {};

      // Determine total duration based on sleep in top-level context only
      lines.forEach((line) => {
        if (!currentThread) {
          const match = line.match(/sleep\s+([\d.]+)/);
          if (match) globalTime += parseFloat(match[1]);
        }
      });
      totalDuration = Math.max(globalTime, 1);
      this.totalDuration = totalDuration;
  
      for (const [loopName, bodyLines] of Object.entries(liveLoopBodies)) {
        const containsStop = bodyLines.some(l => /\bstop\b/.test(l));
        const durationPerIteration = this.estimateDuration(bodyLines) || 4;
        const iterations = Math.floor(this.totalDuration / durationPerIteration);
        const layer = layersMap.get(loopName) || [];

        for (let i = 0; i < iterations; i++) {
          layer.push({
            start: i * durationPerIteration,
            duration: durationPerIteration,
            label: loopName
          });
          if (containsStop) break;
        }
        layersMap.set(loopName, layer);
      }

      globalTime = 0; // reset for second pass
 
      lines.forEach((line, lineIndex) => {
    
        const trimmed = line.trim();
        const liveLoopMatch = trimmed.match(/live_loop\s+(:\w+)/);
        const inThreadMatch = trimmed.match(/in_thread\s+do/);
        const syncMatch = trimmed.match(/sync\s+:?([\w]+)/);
        const sleepMatch = trimmed.match(/sleep\s+([\d.]+)/);
        
        const endMatch = trimmed.match(/\bend\b/);
        const withFxMatch = trimmed.match(/with_fx\s+:?(\w+)/);
        const defineMatch = trimmed.match(/define\s+:?(\w+)/);

        if (defineMatch) {
          const name = defineMatch[1];
          this.defines[name] = true;
        } else if (liveLoopMatch) {
          const name = liveLoopMatch[1].replace(':', '');
          currentThread = {
            name,
            startTime: globalTime,
            currentTime: 0,
            fx: [...fxStack],
            class: 'live-loop',
            index: lineIndex,
            nestingLevel: 0, // Track nesting level
          };
          threads.push(currentThread);
          threadStack.push(currentThread);
        } else if (inThreadMatch) {
          const parent = currentThread;
          const start = parent ? parent.currentTime : globalTime;
          currentThread = {
            name: `in_thread_${threads.length}`,
            startTime: start,
            currentTime: 0,
            fx: [...fxStack],
            class: 'in-thread',
            index: lineIndex,
            nestingLevel: 0, // Track nesting level
          };
          threads.push(currentThread);
          threadStack.push(parent);
        } else if (withFxMatch) {
          fxStack.push(withFxMatch[1]);
        } else if (syncMatch && currentThread) {
          const target = syncMatch[1];
          const syncTime = loopStartTimes[target] ?? 0;
          currentThread.startTime += syncTime;
        } else if (sleepMatch) {
          const duration = parseFloat(sleepMatch[1]);
          if (currentThread) {
            currentThread.currentTime += duration;
          } else {
            globalTime += duration;
          }
        } else if (trimmed.endsWith('do')) {
          // Increment nesting level for nested blocks
          if (currentThread) {
            currentThread.nestingLevel++;
          }
        } else if (endMatch) {
          if (currentThread) {
            if (currentThread.nestingLevel > 0) {
              // Decrement nesting level for nested blocks
              currentThread.nestingLevel--;
            } else {
              // Finalize the current thread when nesting level reaches 0
              const duration = currentThread.currentTime;
              const name = currentThread.name;
              loopStartTimes[name] = currentThread.startTime;

              const fxClass = currentThread.fx.length > 0 ? `fxClass-${currentThread.fx[0]}` : '';
              const codeSnippet = this.parseSonicPiCode(
                lines.slice(currentThread.index, lineIndex + 1).join('\n') // Include the current line with `end`
              );
              const tooltip = `
                <h6>${name}</h6>
                <ul>
                  <li>FX: ${currentThread.fx.join(', ') || 'none'}</li>
                  <li>Duration: ${duration}s</li>
                </ul>
                <pre class="sonic-pi-code"><code>${codeSnippet}</code></pre>
              `;

              layersMap.set(name, [{
                name,
                label: name,
                class: currentThread.class,
                fxClass,
                tooltip,
                infinite: false,
                style: `left: ${(currentThread.startTime / totalDuration) * 100}%; width: ${(duration / totalDuration) * 100}%;`
              }]);

              currentThread = threadStack.pop() || null;
            }
          }
        }
      });

      threads.forEach(thread => {
        if (!layersMap.has(thread.name)) {
          const duration = this.totalDuration - thread.startTime;
          const fxClass = thread.fx.length > 0 ? `fxClass-${thread.fx[0]}` : '';
          const tooltip = `${thread.name}\nFX: ${thread.fx.join(', ') || 'none'}\nDuration: ∞`;

          layersMap.set(thread.name, [{
            name: thread.name,
            label: thread.name,
            class: thread.class,
            fxClass,
            tooltip,
            infinite: true,
            style: `left: ${(thread.startTime / this.totalDuration) * 100}%; width: ${(duration / this.totalDuration) * 100}%;`
          }]);
        }
      });

      const sortedLayers = Array.from(layersMap.entries())
          .sort((a, b) => {
            const aIndex = threads.find(t => t.name === a[0])?.index ?? 0;
            const bIndex = threads.find(t => t.name === b[0])?.index ?? 0;
            return aIndex - bIndex;
          })
          .map(entry => entry[1]);

      this.visualizationLayers = sortedLayers;
    },
  },
};
</script>

<style scoped>
.visualization-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}
.visualization-row {
  display: flex;
  align-items: center;
}
.timeline-row {
  display: flex;
  align-items: center;
  font-size: 0.7rem;
  color: #999;
  margin-bottom: 4px;
}
.timeline-track {
  position: relative;
  height: 16px;
  background: transparent;
  flex: 1;
}
.timeline-tick {
  position: absolute;
  top: 0;
  height: 100%;
  width: 1px;
  border-left: 1px dashed #bbb;
  font-size: 0.65rem;
  text-align: left;
  transform: translateX(-1px);
  white-space: nowrap;
}
.layer-name {
  width: 120px;
  font-weight: bold;
  font-size: 0.85rem;
  text-align: right;
  margin-right: 8px;
  color: #333;
}
.layer-track {
  position: relative;
  flex: 1;
  height: 24px;
  background-color: #f5f5f5;
  border-radius: 4px;
  overflow: visible;
}
.segment-wrapper {
  position: absolute;
  height: 100%;
  top: 0;
}
.segment {
  height: 100%;
  border-radius: 3px;
  text-align: center;
  font-size: 0.75rem;
  color: #9c1c1c;
  padding: 0 4px;
  white-space: nowrap;
  overflow: visible;
  text-overflow: ellipsis;
  position: relative;
  cursor: pointer;
}
.live-loop {
  background-color: #3a86ff;
  color: #fff;
  position: relative;
}

.live-loop::after {
  content: "\f2f9";
  font-family: "Font Awesome 6 Free";
  font-weight: 900;
  margin-left: 5px;
}
.in-thread { background-color: #ff006e; }
.fxClass-reverb { border: 2px dashed #aaa; }
.fxClass-distortion { border: 2px solid red; }
.infinite-loop {
  opacity: 0.7;
  background: linear-gradient(to right, #888 70%, transparent 100%);
}
.custom-tooltip-wrapper {
  position: absolute;
  top: 100%;
  left: 0;
  display: none;
  z-index: 100;
}
.segment:hover .custom-tooltip-wrapper {
  display: block;
}
.custom-tooltip {
  background-color: #fff;
  color: #000;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  text-align: left;
  font-size: 0.75rem;
  max-width: 500px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}
.keyword { color: #d73a49; font-weight: bold; }
.number { color: #005cc5; }
.function { color: #6f42c1; }
.doend { color: #22863a; font-style: italic; }

.time-scale-icons {
  display: flex;
  gap: 8px;
  justify-content: flex-end; /* Align icons to the right */
}

.time-scale-btn {
  background: none;
  border: none;
  font-size: 1.2rem; /* Make icons slightly smaller */
  color: #666;
  cursor: pointer;
  transition: color 0.2s ease;
}

.time-scale-btn.active {
  color: #1A4731;
}

.time-scale-btn:hover {
  color: #278156;
}

</style>