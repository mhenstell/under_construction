class Light {
  int address = -1;
  int value = 0;
  int xpos = 0;
  int ypos = 100;
  int prox = 0;
  
  int tt = -1;
  int rt = -1;
  int rc = -1;
  long last_seen = 0;
  
  color stroke = color(255, 255, 255);
  
  int TIMEOUT = 2000;
  
  Light(int address, int xpos) {
    this.address = address;
    this.xpos = xpos;
  }
  
  void setOutput(int val) {
    this.value = val; 
  }
  
  void touched(boolean state) {
     if (state) {
       this.stroke = color(255, 0, 0);
     } else {
       this.stroke = color(255, 255, 255);
     }
  }
  
  void draw() {
    pushMatrix();
    fill(this.value);
    stroke(this.stroke);
    strokeWeight(2);
    translate(this.xpos, ypos);
    ellipse(0, 0, 50, 50);
    
    if (millis() - this.last_seen > TIMEOUT) {
      fill(255, 0, 0);
      this.prox = 0;
    }
    else fill(255);
    textFont(courier, 18);
    textAlign(CENTER);
    
    if (this.rt > 0) text(this.rt, 0, 50);
    else text("?", 0, 50);
    
    if (this.tt > 0) text(this.tt, 0, 70);
    else text("?", 0, 70);
    
    if (this.rc > 0) text(this.rc, 0, 90);
    else text("?", 0, 90);
    
    int realValue = int(map(this.prox, 0, 255, 0, this.tt));
    text(realValue, 0, -35);
    
    stroke(0, 255, 0);
    strokeWeight(10);
    strokeCap(SQUARE);
    int height = int(map(this.prox, 0, this.tt, -25, 25));
    line(0, 25, 0, -height);
    
    
    popMatrix();
  }
  
  boolean isOver() {
    if (dist(xpos, ypos, mouseX, mouseY) < 50) {
      return true;
    } else {
      return false;
    }
  }
  
  void setProx(int prox) {
    this.prox = prox;
    this.last_seen = millis();
  }
  
  void setConfig(int rt, int tt, int rc) {
    this.rt = rt;
    this.tt = tt;
    this.rc = rc;
  }
}
