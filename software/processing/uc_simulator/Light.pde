class Light {
  int address = -1;
  int value = 0;
  int xpos = 0;
  int ypos = 100;
  
  Light(int address, int xpos) {
    this.address = address;
    this.xpos = xpos;
  }
  
  void setOutput(int val) {
    this.value = val; 
  }
  
  void draw() {
    pushMatrix();
    fill(this.value);
    stroke(255);
    strokeWeight(2);
    translate(this.xpos, ypos);
    ellipse(0, 0, 50, 50);
    popMatrix();
  }
  
  boolean isOver() {
    if (dist(xpos, ypos, mouseX, mouseY) < 50) {
      return true;
    } else {
      return false;
    }
  }
  
  void clicked() {
     
  }
  
  
}
