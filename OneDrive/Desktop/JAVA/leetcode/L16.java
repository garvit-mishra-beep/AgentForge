class L16 {
    public int threeSumClosest(int[] nums, int target) {
        Arrays.sort(nums);
        int n = nums.length;
        int result = 0;
        int max_diff = Integer.MAX_VALUE;
        for(int i = 0; i< n -2; i++){
            int left = i + 1;
            int right = n -1;
            int diff = 0;
            while(left < right) {
                int total = nums[i] + nums[left] + nums[right];
                diff = Math.abs(total - target);
                if(diff < max_diff){
                    max_diff = diff;
                    result = total;
                }

                if(total == target) {
                    return result;
                }
                else if(total < target) {
                    left++;
                }
                else{
                    right--;
                }
            }
        }
        return result;
    }
} 