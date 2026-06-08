public class Freq {
    public static void main(String[] args) {
        int[] numbers = {1,1,1,1,1,5,6,2,4,4,2,3,5,6,7,8,9,1,4,5};
        int[] frequency = new int[10]; 
        for (int n : numbers) {
            frequency[n]++;
        }
        System.out.println("Number Frequency:");
        for (int i = 0; i < frequency.length; i++) {
            if (frequency[i] > 0) {
                System.out.println("Number: " + i + ", Frequency: " + frequency[i]);
            }
        }
    }
}
