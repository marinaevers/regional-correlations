<template>
  <div class="card" style="user-select: none;">
    <h5 class="card-header"><a @click="reset">Statistics <small>(<a>load</a>)</small></a>
      <span class="float-right"><small><a @click="show = !show"><span v-if="show">hide</span><span
        v-else>show</span></a></small></span>
    </h5>
    <div class="card-body" v-show="show">
      <canvas ref="canvas"></canvas>
      <input v-model="max_count" @change="invalidate" style="display: none">
    </div>
    <div class="card-footer">
      <div class="row">
        <div class="col-sm-3">
          <label><input type="checkbox" v-model="yearly" @change="updateAxis"> Show yearly x-axis ticks </label>
        </div>
        <div class="col-sm-3">
          <input v-model="xLabel" class="form-control" placeholder="x label">
        </div>
        <div class="col-sm-3">
          <input v-model="yLabel" class="form-control" placeholder="y label">
        </div>
        <div class="col-sm-3">
          <input v-model="fontsize" class="form-control" placeholder="fontsize">
        </div>
      </div>
    </div>
    <!--    <div class="card-footer" v-show="show">-->
    <!--      <a class="btn btn-secondary btn-sm" v-for="s in statistics">{{ s }}</a>-->
    <!--    </div>-->
  </div>
</template>

<script>
const Chart = require('chart.js')
// import { Chart } from 'chart.js';
require('hammerjs')
require('chartjs-plugin-zoom')
// import 'chartjs-plugin-zoom'
Chart.defaults.stripe = Chart.helpers.clone(Chart.defaults.line);
Chart.controllers.stripe = Chart.controllers.line.extend({
  draw: function (ease) {
    var result = Chart.controllers.line.prototype.draw.apply(this, arguments);

    // don't render the stripes till we've finished animating
    if (!this.rendered && ease !== 1)
      return;
    this.rendered = true;


    var helpers = Chart.helpers;
    var meta = this.getMeta();
    var yScale = this.getScaleForId(meta.yAxisID);
    var yScaleZeroPixel = yScale.getPixelForValue(0);
    var widths = this.getDataset().width;
    var ctx = this.chart.chart.ctx;

    ctx.save();
    ctx.fillStyle = this.getDataset().backgroundColor;
    ctx.lineWidth = 1;
    ctx.beginPath();

    // initialize the data and bezier control points for the top of the stripe
    helpers.each(meta.data, function (point, index) {
      point._view.y += (yScale.getPixelForValue(widths[index]) - yScaleZeroPixel);
    });
    Chart.controllers.line.prototype.updateBezierControlPoints.apply(this);

    // draw the top of the stripe
    helpers.each(meta.data, function (point, index) {
      if (index === 0)
        ctx.moveTo(point._view.x, point._view.y);
      else {
        var previous = helpers.previousItem(meta.data, index);
        var next = helpers.nextItem(meta.data, index);

        Chart.elements.Line.prototype.lineToNextPoint.apply({
          _chart: {
            ctx: ctx
          }
        }, [previous, point, next, null, null])
      }
    });

    // revert the data for the top of the stripe
    // initialize the data and bezier control points for the bottom of the stripe
    helpers.each(meta.data, function (point, index) {
      point._view.y -= 2 * (yScale.getPixelForValue(widths[index]) - yScaleZeroPixel);
    });
    // we are drawing the points in the reverse direction
    meta.data.reverse();
    Chart.controllers.line.prototype.updateBezierControlPoints.apply(this);

    // draw the bottom of the stripe
    helpers.each(meta.data, function (point, index) {
      if (index === 0)
        ctx.lineTo(point._view.x, point._view.y);
      else {
        var previous = helpers.previousItem(meta.data, index);
        var next = helpers.nextItem(meta.data, index);

        Chart.elements.Line.prototype.lineToNextPoint.apply({
          _chart: {
            ctx: ctx
          }
        }, [previous, point, next, null, null])
      }

    });

    // revert the data for the bottom of the stripe
    meta.data.reverse();
    helpers.each(meta.data, function (point, index) {
      point._view.y += (yScale.getPixelForValue(widths[index]) - yScaleZeroPixel);
    });
    Chart.controllers.line.prototype.updateBezierControlPoints.apply(this);

    ctx.stroke();
    ctx.closePath();
    ctx.fill();
    ctx.restore();

    return result;
  }
});

export default {
  components: {},
  props: {
    labels: {}
  },
  data() {
    return {
      show: true,
      ctx: null,
      chart: null,
      scale: 'linear',
      statistics: ['median', 'lower_quartile', 'upper_quartile', 'lower_bound', 'upper_bound', 'outliers'],
      statistic: 'median',
      max_count: 1000,
      yearly: false,
      xLabel: 'x',
      yLabel: 'value',
      fontsize: 16,
    }
  },
  computed: {
    curves() {
      return this.$store.state.vis.details
    }
  },
  watch: {
    '$store.state.vis.details'() {
      this.invalidate()
    },
    statistic() {
      this.invalidate()
    }
  },
  created() {
  },
  mounted() {
    this.ctx = this.$refs.canvas.getContext('2d');
    this.invalidate()
  },
  methods: {
    reset() {
      this.$store.dispatch('vis/fetchDetails', this.$parent.level)
      this.invalidate()
    },
    invalidate() {
      if (this.chart !== null) {
        this.chart.clear()
        this.chart.destroy();
      }
      let datasets = this.getDatasets(this.statistic)
      this.chart = new Chart(this.ctx, {
        // type: 'line',
        data: {
          labels: this.getLabels(),
          datasets: datasets
        },
        options: {
          hover: {
            mode: 'nearest',
            intersect: false
          },
          responsive: true,
          title: {
            display: false,
            text: "Chart.js HUGE data set"
          },
          scales: {
            xAxes: [
              {
                scaleLabel: {
                  display: true,
                  labelString: this.xLabel,
                  fontSize: this.fontsize,
                },
                ticks: {
                  fontSize: this.fontsize,
                  maxRotation: 0,
                  autoSkip: true,
                  callback: (value, index, values) => {
                    if (!this.yearly) return value
                    if (value % 12 === 0) return value / 12
                    return null
                    // return '$' + value;
                  }
                }
              }
            ],
            yAxes: [
              {
                scaleLabel: {
                  display: true,
                  labelString: this.yLabel,
                  fontSize: this.fontsize,
                },
                ticks: {
                  fontSize: this.fontsize,
                }
              }
            ]
          },
          pan: {
            enabled: true,
            mode: "x",
            speed: 10,
            threshold: 10
          },
          zoom: {
            enabled: true,
            drag: false,
            mode: "xy",
            speed: 0.3,
            // sensitivity: 0.1,
            limits: {
              max: 10,
              min: 0.5
            }
          }
        },

      });
    },
    getDatasets(statistic) {
      let datasets = []
      let mini = 9999
      let maxi = -9999
      let max_count = this.max_count
      for (let segment in this.curves) {
        let label = this.labels[segment] ? this.labels[segment] + '_' : ''
        let median = {
          type: 'line',
          label: label + 'median',
          data: JSON.parse(JSON.stringify(this.curves[segment]['median'])).slice(0, max_count),
          // borderColor: 'transparent',
          borderColor: `rgba(${this.curves[segment].color[0]}, ${this.curves[segment].color[1]}, ${this.curves[segment].color[2]})`,
          //backgroundColor: `rgba(${this.curves[segment].color[0]}, ${this.curves[segment].color[1]}, ${this.curves[segment].color[2]}, 0.4)`,
          borderWidth: 2,
          fill: false,
          tension: 0,
          // width: JSON.parse(JSON.stringify(this.curves[segment].width)),
          pointRadius: 0
        }
        let lower_quartile = {
          label: label + 'min',
          type: 'line',
          data: JSON.parse(JSON.stringify(this.curves[segment]['lower_quartile'])).slice(0, max_count),
          borderColor: 'transparent',
          // borderColor: `rgba(${this.curves[segment].color[0]}, ${this.curves[segment].color[1]}, ${this.curves[segment].color[2]})`,
          backgroundColor: `rgba(${this.curves[segment].color[0]}, ${this.curves[segment].color[1]}, ${this.curves[segment].color[2]}, 0.4)`,
          // borderWidth: 1,
          fill: datasets.length,
          //tension: 0,
          // width: JSON.parse(JSON.stringify(this.curves[segment].width)),
          pointRadius: 0
        }
        let upper_quartile = {
          label: label + 'max',
          type: 'line',
          data: JSON.parse(JSON.stringify(this.curves[segment]['upper_quartile'])).slice(0, max_count),
          borderColor: 'transparent',
          // borderColor: `rgba(${this.curves[segment].color[0]}, ${this.curves[segment].color[1]}, ${this.curves[segment].color[2]})`,
          backgroundColor: `rgba(${this.curves[segment].color[0]}, ${this.curves[segment].color[1]}, ${this.curves[segment].color[2]}, 0.4)`,
          // borderWidth: 1,
          fill: datasets.length,
          //tension: 0,
          pointRadius: 0
        }
        // for
        // let outliers = {
        //   label: label + 'out',
        //   type: 'line',
        //   data: JSON.parse(JSON.stringify(this.curves[segment]['outliers'])),
        //   // borderColor: 'transparent',
        //   borderColor: `rgba(${this.curves[segment].color[0]}, ${this.curves[segment].color[1]}, ${this.curves[segment].color[2]})`,
        //   backgroundColor: `rgba(${this.curves[segment].color[0]}, ${this.curves[segment].color[1]}, ${this.curves[segment].color[2]}, 0.4)`,
        //   borderWidth: 1,
        //   fill: null,
        //   tension: 0,
        //   pointRadius: 1
        // }
        // mini = Math.min(this.curves[segment].median)
        datasets.push(median)
        datasets.push(lower_quartile)
        datasets.push(upper_quartile)
        // datasets.push(outliers)
        // mini = Math.min(this.curves[segment].median)
      }
      return datasets
    },
    getLabels() {
      let labels = []
      for (let segment in this.curves) {
        console.log(this.curves[segment].median.length)
        labels = new Array(this.curves[segment].median.slice(0, this.max_count).length)
        for (let i = 0; i < labels.length; i++) {
          labels[i] = i
        }
      }
      return labels
    },
    updateAxis() {
      this.invalidate()
      console.log(this.yearly)
    }
  }
}
</script>
