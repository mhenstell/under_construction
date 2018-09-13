import redis.clients.jedis.JedisPubSub;

class RedisListener extends JedisPubSub {
  
  void onMessage(String channel, String message) {
     println(channel + ": " + message);
     
     String[] outputGroups = match(message, "(\\d*):LIGHT_LEVEL:(\\d*)");
     if (outputGroups != null) {
        int addr = int(outputGroups[1]);
        int val = int(outputGroups[2]);
        lights.get(addr).setOutput(val);
     }
     
  }
}
