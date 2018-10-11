import de.voidplus.redis.*;

int numLights = 10;

Redis sub_redis;
Redis pub_redis;
HashMap<Integer, Light> lights;
HashMap<Integer, Button> buttons;

PFont courier;

void redisThread() {
  RedisListener rl = new RedisListener();
  sub_redis.subscribe(rl, "uc");
}

void setup() {
  size(725, 200);
  background(0);
  noStroke();
  smooth(2);

  courier = loadFont("Courier-12.vlw");
  String redis_host = "127.0.0.1";
  
  sub_redis = new Redis(this, redis_host, 6379);
  pub_redis = new Redis(this, redis_host, 6379);

  thread("redisThread");

  lights = new HashMap<Integer, Light>();
  for (int x = 0; x < numLights; x++) {
    lights.put(x, new Light(x, 70 * x + 50));
  }

  buttons = new HashMap<Integer, Button>();
  Button reload = new Button("Reload", width - 100, 10);
  buttons.put(0, reload);
}

void draw() {
  background(0);
  for (int idx = 0; idx < numLights; idx++) {
    lights.get(idx).draw();
  }

  for (int idx = 0; idx < buttons.size(); idx++) {
    buttons.get(idx).draw();
  }
  fill(255);
  textFont(courier, 18);
  textAlign(LEFT);
  text("RT", 0, 150);
  text("TT", 0, 170);
  text("RC", 0, 190);
}

void mousePressed() {
  for (int idx = 0; idx < numLights; idx++) {
    if (lights.get(idx).isOver() == true) {      
      pub_redis.publish("uc", idx + ":TOUCH_TRIG:255");
    }
  }

  for (int idx = 0; idx < buttons.size(); idx++) {
    if (buttons.get(idx).isOver() == true) {      
      buttons.get(idx).mouseDown(true);
      pub_redis.publish("uc", "99:" + buttons.get(idx).name.toUpperCase() + ":0");
    }
  }
}

void mouseReleased() {
  for (int idx = 0; idx < numLights; idx++) {
    if (lights.get(idx).isOver() == true) {
      pub_redis.publish("uc", idx + ":TOUCH_UNTRIG:0");
    }
  }

  for (int idx = 0; idx < buttons.size(); idx++) {
    if (buttons.get(idx).isOver() == true) {      
      buttons.get(idx).mouseDown(false);
    }
  }
}
