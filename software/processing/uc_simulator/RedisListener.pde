import redis.clients.jedis.JedisPubSub;

class RedisListener extends JedisPubSub {
  
  void onMessage(String channel, String message) {
     println(channel + ": " + message);
     
     String[] outputGroups = match(message, "(\\d*):LIGHT_LEVEL:(\\d*)");
     if (outputGroups != null) {
        int addr = int(outputGroups[1]);
        int val = int(outputGroups[2]);
        if (addr < 0 || addr > 9) return;        
        lights.get(addr).setOutput(val);
     }
     
     outputGroups = match(message, "(\\d*):ALL_LEVEL:(\\d*):(\\d*):(\\d*):(\\d*):(\\d*):(\\d*):(\\d*):(\\d*):(\\d*):(\\d*)");
     if (outputGroups != null) {
       for (int x = 0; x < 10; x++) {
        lights.get(x).setOutput(int(outputGroups[x + 2])); 
        //println("Light " + x + " Level " + int(outputGroups[x+2]));
       }
     }
     
     outputGroups = match(message, "(\\d*):PROX:(\\d*)");
     if (outputGroups != null) {
        int addr = int(outputGroups[1]);
        int val = int(outputGroups[2]);
        if (addr < 0 || addr > 9) return;        
        if (val > 0) lights.get(addr).touched(true);
        else lights.get(addr).touched(false);
     }
     
     outputGroups = match(message, "(\\d*):PROX_SIM:(\\d*)");
     if (outputGroups != null) {
        int addr = int(outputGroups[1]);
        int val = int(outputGroups[2]);
        if (addr < 0 || addr > 9) return;        
        lights.get(addr).setProx(val);
     }
     
     outputGroups = match(message, "(\\d*):ACK_CONFIG_SIM:(\\d*):(\\d*):(\\d*)");
     if (outputGroups != null) {
        int addr = int(outputGroups[1]);
        if (addr < 0 || addr > 9) return;
        
        int rt = int(outputGroups[2]);
        int tt = int(outputGroups[3]);
        int rc = int(outputGroups[4]);
        
        lights.get(addr).setConfig(rt, tt, rc);
     }
     
  }
}
