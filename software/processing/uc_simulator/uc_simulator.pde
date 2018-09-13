import de.voidplus.redis.*;

int numLights = 10;

Redis sub_redis;
Redis pub_redis;
HashMap<Integer, Light> lights;

void redisThread() {
    RedisListener rl = new RedisListener();
    sub_redis.subscribe(rl, "uc");
}

void setup(){
    size(725, 200);
    background(0);
    noStroke();
    smooth(2);
    
    sub_redis = new Redis(this, "127.0.0.1", 6379);
    pub_redis = new Redis(this, "127.0.0.1", 6379);

    thread("redisThread");
    
    lights = new HashMap<Integer, Light>();
    for (int x = 0; x < numLights; x++) {
      lights.put(x, new Light(x, 70 * x + 50));
    }

}

void draw() {
  
  for (int idx = 0; idx < numLights; idx++) {
    lights.get(idx).draw();     
  }
}

void mousePressed() {
  for (int idx = 0; idx < numLights; idx++) {
    if (lights.get(idx).isOver() == true) {      
      pub_redis.publish("uc", idx + ":PROX:0");
    }
  }
}

void mouseReleased() {
  for (int idx = 0; idx < numLights; idx++) {
    if (lights.get(idx).isOver() == true) {
      pub_redis.publish("uc", idx + ":PROX:65535");      
    }
  }
}
